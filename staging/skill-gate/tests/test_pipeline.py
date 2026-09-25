"""run → judge → receipt → verify-receipt, with the model judge faked."""

import json
import re
import shutil

import pytest
import yaml

from skillgate.cases import assign_splits
from skillgate.config import load_config
from skillgate.criteria import ratify
from skillgate.judge import judge_run
from skillgate.llm import LLMError
from skillgate.receipt import build_receipt
from skillgate.run import create_manual_run
from skillgate.util import SkillGateError, read_json
from skillgate.verify import verify_receipt
from tests.conftest import EXAMPLE, FakeModel, fill_outputs, make_project

GOOD = lambda cid, r: f"OK {cid}\n"  # noqa: E731


def _prepare(root, k=2, **kw):
    make_project(root, **kw)
    cfg = load_config(root / "skillgate.yaml")
    assign_splits(cfg.paths["cases"], cfg.paths["golden"], 0.3, seed=11)
    ratify(cfg.paths["criteria"], "Dana Expert")
    run_dir, _ = create_manual_run(cfg, k=k)
    return cfg, run_dir


def _pass_model():
    def responder(user, n):
        output = re.search(r"<output>\n(.*?)\n</output>", user, re.S).group(1)
        return {"verdict": "PASS", "reason": "One line.", "evidence": output.strip().splitlines()[0]}
    return FakeModel(responder)


def test_all_deterministic_and_passing_is_verified(tmp_path):
    cfg, run_dir = _prepare(tmp_path / "p")
    fill_outputs(run_dir, GOOD)
    judge_run(cfg, run_dir)
    r = read_json(build_receipt(cfg) / "receipt.json")
    assert r["verdict"] == "VERIFIED", r["reasons"]
    assert r["calibration"]["status"] == "NOT APPLICABLE"
    assert r["results"]["by_split"]["holdout"]["passed"] == 3


def test_a_single_failing_repeat_makes_the_case_flaky_and_blocks_verified(tmp_path):
    cfg, run_dir = _prepare(tmp_path / "p")
    fill_outputs(run_dir, lambda cid, r: "OK wrong\n" if (cid, r) == ("c01", 2) else GOOD(cid, r))
    judge_run(cfg, run_dir)
    r = read_json(build_receipt(cfg) / "receipt.json")
    assert r["verdict"] == "NOT VERIFIED"
    fc = next(f for f in r["failing_cases"] if f["case_id"] == "c01")
    assert fc["status"] == "FLAKY"
    assert [m["case_id"] for m in r["misses"]] == ["c01"]  # c01's E1 is a detect expectation


def test_single_run_withholds_verified(tmp_path):
    cfg, run_dir = _prepare(tmp_path / "p", k=1)
    fill_outputs(run_dir, GOOD)
    judge_run(cfg, run_dir)
    r = read_json(build_receipt(cfg) / "receipt.json")
    assert "SINGLE RUN" in r["flags"] and r["verdict"] == "NOT VERIFIED"


def test_forced_api_failure_is_error_not_fail_and_blocks_verified(tmp_path):
    cfg, run_dir = _prepare(tmp_path / "p", model_expectation=True)
    fill_outputs(run_dir, GOOD)
    model = FakeModel(lambda user, n: LLMError("API error 529: overloaded"))
    judge_dir = judge_run(cfg, run_dir, model_factory=lambda: model)
    judgments = [j for f in (judge_dir / "judgments").rglob("*.json") for j in read_json(f)]
    model_js = [j for j in judgments if j["method"] == "model"]
    assert model_js and all(j["verdict"] == "ERROR" for j in model_js)
    assert not any(j["verdict"] == "FAIL" for j in judgments)
    r = read_json(build_receipt(cfg) / "receipt.json")
    assert r["verdict"] == "NOT VERIFIED"
    assert r["results"]["totals"]["ERROR"] == len(model_js)
    assert any("ERROR" in x for x in r["reasons"])
    assert all(pc["status"] == "ERROR" for pc in r["failing_cases"])


def test_evidence_not_in_output_is_reasked_once_then_error(tmp_path):
    cfg, run_dir = _prepare(tmp_path / "p", n=10, model_expectation=True)
    fill_outputs(run_dir, GOOD)
    model = FakeModel(lambda user, n: {"verdict": "PASS", "reason": "x", "evidence": "text the output never said"})
    judge_dir = judge_run(cfg, run_dir, model_factory=lambda: model)
    js = [j for f in (judge_dir / "judgments").rglob("*.json") for j in read_json(f) if j["method"] == "model"]
    assert all(j["verdict"] == "ERROR" and j["attempts"] == 2 for j in js)
    assert "not found in the output" in js[0]["reason"]
    assert sum("could not be accepted" in c["user"] for c in model.calls) == len(js)  # one re-ask each


def test_reask_can_recover(tmp_path):
    cfg, run_dir = _prepare(tmp_path / "p", model_expectation=True)
    fill_outputs(run_dir, GOOD)

    def responder(user, n):
        output = re.search(r"<output>\n(.*?)\n</output>", user, re.S).group(1).strip()
        if "could not be accepted" in user:
            return {"verdict": "PASS", "reason": "ok", "evidence": output}
        return {"verdict": "PASS", "reason": "ok", "evidence": "invented"}

    judge_dir = judge_run(cfg, run_dir, model_factory=lambda: FakeModel(responder))
    js = [j for f in (judge_dir / "judgments").rglob("*.json") for j in read_json(f) if j["method"] == "model"]
    assert all(j["verdict"] == "PASS" and j["attempts"] == 2 for j in js)


def test_judge_sees_output_input_and_one_check_only(tmp_path):
    cfg, run_dir = _prepare(tmp_path / "p", model_expectation=True)
    fill_outputs(run_dir, GOOD)
    model = _pass_model()
    judge_run(cfg, run_dir, model_factory=lambda: model)
    prompt = model.calls[0]["user"]
    assert "<input>" in prompt and "<output>" in prompt and "<check>" in prompt
    assert "SECRET-NOTE" not in prompt  # the author's notes on the case
    assert "The output says OK" not in prompt  # other checks on the same case
    assert "PASS" not in prompt.split("<check>")[0]  # no earlier verdicts


def test_model_judged_run_is_uncalibrated_and_records_cost(tmp_path):
    cfg, run_dir = _prepare(tmp_path / "p", model_expectation=True)
    fill_outputs(run_dir, GOOD)
    judge_dir = judge_run(cfg, run_dir, model_factory=_pass_model)
    meta = read_json(judge_dir / "judge.json")
    assert meta["calls"]["model_calls"] == 20 and meta["calls"]["cost_usd"] == pytest.approx(20 * (100 * 5 + 20 * 25) / 1e6)
    log = [json.loads(line) for line in (judge_dir / "log.jsonl").read_text().splitlines()]
    assert sum(e["event"] == "model_call" for e in log) == 20
    r = read_json(build_receipt(cfg) / "receipt.json")
    assert "JUDGE UNCALIBRATED" in r["flags"] and r["verdict"] == "NOT VERIFIED"


def test_empty_output_is_error(tmp_path):
    cfg, run_dir = _prepare(tmp_path / "p")
    fill_outputs(run_dir, lambda cid, r: "" if cid == "c02" else GOOD(cid, r))
    judge_dir = judge_run(cfg, run_dir)
    js = read_json(judge_dir / "judgments" / "c02" / "1.json")
    assert {j["verdict"] for j in js} == {"ERROR"}


def test_runs_and_receipts_are_never_overwritten(tmp_path):
    cfg, run_dir = _prepare(tmp_path / "p")
    fill_outputs(run_dir, GOOD)
    judge_run(cfg, run_dir)
    out = build_receipt(cfg)
    with pytest.raises(SkillGateError, match="never overwrites"):
        from skillgate.util import new_dir
        new_dir(out)


def test_receipt_refuses_when_an_output_changed_after_judging(tmp_path):
    cfg, run_dir = _prepare(tmp_path / "p")
    fill_outputs(run_dir, GOOD)
    judge_run(cfg, run_dir)
    (run_dir / "outputs" / "c01" / "1.md").write_text("OK c01 \n")
    with pytest.raises(SkillGateError, match="changed after it was judged"):
        build_receipt(cfg)


def test_holdout_details_are_redacted(tmp_path):
    cfg, run_dir = _prepare(tmp_path / "p")
    fill_outputs(run_dir, lambda cid, r: "OK nope\n")
    judge_run(cfg, run_dir)
    out = build_receipt(cfg)
    r = read_json(out / "receipt.json")
    holdout = [f for f in r["failing_cases"] if f["split"] == "holdout"]
    assert holdout and all(ch["details"] == "redacted (holdout)" for f in holdout for ch in f["checks"])
    md = (out / "receipt.md").read_text()
    for f in holdout:
        assert f"case {f['case_id']}" not in md  # the holdout input text never appears
    sheet = (run_dir / "run_sheet.dev.md").read_text()
    assert not any(f"case {f['case_id']}" in sheet for f in holdout)


def _verified_receipt(tmp_path):
    cfg, run_dir = _prepare(tmp_path / "p")
    fill_outputs(run_dir, GOOD)
    judge_run(cfg, run_dir)
    return cfg, run_dir, build_receipt(cfg)


def test_clean_receipt_verifies(tmp_path):
    _, _, out = _verified_receipt(tmp_path)
    problems, checked = verify_receipt(out / "receipt.json")
    assert problems == [] and checked > 20


def test_one_byte_edit_to_an_output_is_detected(tmp_path):
    _, run_dir, out = _verified_receipt(tmp_path)
    f = run_dir / "outputs" / "c03" / "2.md"
    data = bytearray(f.read_bytes())
    data[0] ^= 0x01
    f.write_bytes(bytes(data))
    problems, _ = verify_receipt(out / "receipt.json")
    assert any("outputs/c03/2.md" in p and "mismatch" in p for p in problems)


def test_edited_verdict_is_detected_even_with_a_recomputed_hash(tmp_path):
    from skillgate.receipt import consistency_hash, render_md
    from skillgate.util import write_json

    cfg, run_dir = _prepare(tmp_path / "p")
    fill_outputs(run_dir, lambda cid, r: "OK wrong\n" if cid == "c01" else GOOD(cid, r))
    judge_run(cfg, run_dir)
    out = build_receipt(cfg)
    r = read_json(out / "receipt.json")
    assert r["verdict"] == "NOT VERIFIED"
    r.update(verdict="VERIFIED", reasons=[])
    r["consistency_sha256"] = consistency_hash(r)
    write_json(out / "receipt.json", r)
    (out / "receipt.md").write_text(render_md(r))
    problems, _ = verify_receipt(out / "receipt.json")
    assert any(p.startswith("verdict: recomputes to NOT VERIFIED") for p in problems)


def test_edited_judgment_is_detected(tmp_path):
    _, run_dir, out = _verified_receipt(tmp_path)
    jf = next((next(run_dir.glob("judge-*")) / "judgments").rglob("*.json"))
    js = read_json(jf)
    js[0]["verdict"] = "FAIL"
    jf.write_text(json.dumps(js))
    problems, _ = verify_receipt(out / "receipt.json")
    assert any("mismatch" in p for p in problems) and any(p.startswith("results.") for p in problems)


def test_edited_receipt_md_is_detected(tmp_path):
    _, _, out = _verified_receipt(tmp_path)
    md = out / "receipt.md"
    md.write_text(md.read_text().replace("## Verdict: VERIFIED", "## Verdict: VERIFIED (great!)"))
    problems, _ = verify_receipt(out / "receipt.json")
    assert "receipt.md: does not match receipt.json" in problems


AVERAGE_WORDS = re.compile(r"\b(average|averaged|mean|score|scores|pass rate|accuracy)\b|%", re.I)


def test_no_output_file_contains_an_averaged_score(tmp_path):
    cfg, run_dir = _prepare(tmp_path / "p", model_expectation=True)
    fill_outputs(run_dir, lambda cid, r: "OK wrong\n" if cid == "c01" else GOOD(cid, r))
    judge_dir = judge_run(cfg, run_dir, model_factory=_pass_model)
    out = build_receipt(cfg)
    files = [out / "receipt.md", out / "receipt.json", judge_dir / "summary.json", judge_dir / "report.md"]
    for f in files:
        text = f.read_text()
        if f.suffix == ".json":
            keys = re.findall(r'"([a-z_]+)":', text)
            assert not [k for k in keys if AVERAGE_WORDS.search(k.replace("_", " "))], f
        else:
            hits = [m.group(0) for m in AVERAGE_WORDS.finditer(text)]
            assert hits == [], (f, hits)


def test_committed_example_receipt_verifies():
    receipts = sorted((EXAMPLE / "receipts").glob("*/receipt.json"))
    assert receipts, "the example receipt is committed"
    for r in receipts:
        problems, _ = verify_receipt(r)
        assert problems == [], problems


def test_example_project_end_to_end(example_copy):
    cfg = load_config(example_copy / "skillgate.yaml")
    run_dir, _ = create_manual_run(cfg)
    src = EXAMPLE / "fixture-outputs"
    shutil.copytree(src, run_dir / "outputs", dirs_exist_ok=True, ignore=shutil.ignore_patterns("capture.yaml"))
    shutil.copy(src / "capture.yaml", run_dir / "capture.yaml")
    judge_run(cfg, run_dir)
    r = read_json(build_receipt(cfg) / "receipt.json")
    committed = read_json(sorted((EXAMPLE / "receipts").glob("*/receipt.json"))[-1])
    for key in ("verdict", "reasons", "results", "misses", "false_flags"):
        assert r[key] == committed[key], key

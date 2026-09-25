"""Milestone 3: estimate and budget, API mode with caching, calibration, and staleness."""

import csv
import re
import shutil

import pytest
import yaml

from skillgate import prompts as prompts_module
from skillgate.calibrate import export_sheet, import_labels
from skillgate.cases import assign_splits
from skillgate.cli import main
from skillgate.config import load_config
from skillgate.criteria import ratify
from skillgate.executor import ExecutorError
from skillgate.judge import judge_run
from skillgate.receipt import build_receipt
from skillgate.run import create_api_run, create_manual_run
from skillgate.stale import check_stale
from skillgate.util import SkillGateError, read_json, write_json
from skillgate.verify import verify_receipt
from tests.conftest import FakeExecutor, FakeModel, add_executor, fill_outputs, make_project


def _api_project(root, **kw):
    make_project(root, **kw)
    add_executor(root)
    cfg = load_config(root / "skillgate.yaml")
    assign_splits(cfg.paths["cases"], cfg.paths["golden"], 0.3, seed=11)
    ratify(cfg.paths["criteria"], "Dana Expert")
    return cfg


def _set(root, path, value):
    cfg_path = root / "skillgate.yaml"
    data = yaml.safe_load(cfg_path.read_text())
    node = data
    for key in path[:-1]:
        node = node.setdefault(key, {})
    node[path[-1]] = value
    cfg_path.write_text(yaml.safe_dump(data, sort_keys=False))
    return load_config(cfg_path)


# --- estimate and budget ---------------------------------------------------------------------

def test_budget_cap_aborts_an_over_budget_run_before_any_call(tmp_path):
    root = tmp_path / "p"
    _api_project(root)
    cfg = _set(root, ["budget", "max_usd"], 0.0001)
    made = []
    with pytest.raises(SkillGateError, match="above the budget"):
        create_api_run(cfg, executor_factory=lambda: made.append(1) or FakeExecutor())
    assert made == [] and not (root / "runs").exists()


def test_confirm_budget_lets_an_over_budget_run_proceed(tmp_path):
    root = tmp_path / "p"
    _api_project(root)
    cfg = _set(root, ["budget", "max_usd"], 0.0001)
    run_dir, ex = create_api_run(cfg, confirm_budget=True, executor_factory=FakeExecutor)
    assert ex["calls"] == 20 and (run_dir / "execution.json").is_file()


def test_paid_step_without_budget_or_price_is_refused(tmp_path):
    root = tmp_path / "p"
    _api_project(root)
    cfg = _set(root, ["budget"], {})
    with pytest.raises(SkillGateError, match="budget.max_usd"):
        create_api_run(cfg, executor_factory=FakeExecutor)
    _set(root, ["budget"], {"max_usd": 5})
    cfg = _set(root, ["pricing"], {"claude-opus-5": {"input_per_mtok": 5, "output_per_mtok": 25}})
    with pytest.raises(SkillGateError, match="No price for model 'gemini-test-001'"):
        create_api_run(cfg, executor_factory=FakeExecutor)


def test_estimate_counts_calls_and_the_cli_flags_over_budget(tmp_path, capsys, monkeypatch):
    root = tmp_path / "p"
    _api_project(root, model_checks=2)
    monkeypatch.chdir(root)
    assert main(["estimate", "--mode", "api"]) == 0
    out = capsys.readouterr().out
    assert "20 call(s) (0 cached" in out  # 10 cases x 2 repeats
    assert "judge claude-opus-5: 40 call(s)" in out  # 2 model-judged checks per case per repeat
    _set(root, ["budget", "max_usd"], 0.0001)
    main(["estimate", "--mode", "api"])
    assert "OVER BUDGET" in capsys.readouterr().out


def test_judge_step_also_respects_the_budget(tmp_path):
    root = tmp_path / "p"
    make_project(root, model_expectation=True)
    cfg = load_config(root / "skillgate.yaml")
    assign_splits(cfg.paths["cases"], cfg.paths["golden"], 0.3, seed=11)
    ratify(cfg.paths["criteria"], "Dana")
    run_dir, _ = create_manual_run(cfg)
    fill_outputs(run_dir, lambda cid, r: f"OK {cid}\n")
    cfg = _set(root, ["budget", "max_usd"], 0.00001)
    model = FakeModel(lambda u, n: {"verdict": "PASS", "reason": "r", "evidence": "OK"})
    with pytest.raises(SkillGateError, match="above the budget"):
        judge_run(cfg, run_dir, model_factory=lambda: model)
    assert model.calls == []


# --- API mode and the cache ------------------------------------------------------------------

def test_cache_prevents_repeat_calls(tmp_path):
    root = tmp_path / "p"
    cfg = _api_project(root)
    first = FakeExecutor()
    run1, ex1 = create_api_run(cfg, executor_factory=lambda: first)
    assert first.calls == 20 and ex1["cache_hits"] == 0
    second = FakeExecutor()
    run2, ex2 = create_api_run(cfg, executor_factory=lambda: second)
    assert second.calls == 0 and ex2["calls"] == 0 and ex2["cache_hits"] == 20
    assert run1 != run2  # a new run directory; nothing overwritten
    assert (run1 / "outputs" / "c01" / "1.md").read_text() == (run2 / "outputs" / "c01" / "1.md").read_text()


def test_changed_settings_or_skill_miss_the_cache(tmp_path):
    root = tmp_path / "p"
    cfg = _api_project(root)
    create_api_run(cfg, executor_factory=FakeExecutor)
    cfg = _set(root, ["executor", "settings", "temperature"], 0.2)
    ex = FakeExecutor()
    create_api_run(cfg, executor_factory=lambda: ex)
    assert ex.calls == 20
    (root / "skill.md").write_text((root / "skill.md").read_text() + "\nAlways be brief.\n")
    ex = FakeExecutor()
    create_api_run(load_config(root / "skillgate.yaml"), executor_factory=lambda: ex)
    assert ex.calls == 20


def test_executor_failure_is_error_in_judging_and_is_not_cached(tmp_path):
    root = tmp_path / "p"
    cfg = _api_project(root)

    def fn(user):
        cid = user.split("case ")[-1].split()[0]
        return ExecutorError("API error 503: unavailable") if cid == "c02" else f"OK {cid}"

    run_dir, ex = create_api_run(cfg, executor_factory=lambda: FakeExecutor(fn))
    assert ex["errors"] == 2
    judge_dir = judge_run(cfg, run_dir)
    js = read_json(judge_dir / "judgments" / "c02" / "1.json")
    assert {j["verdict"] for j in js} == {"ERROR"} and "503" in js[0]["reason"]
    r = read_json(build_receipt(cfg) / "receipt.json")
    assert r["verdict"] == "NOT VERIFIED" and r["results"]["totals"]["ERROR"] > 0
    retry = FakeExecutor()
    create_api_run(cfg, executor_factory=lambda: retry)
    assert retry.calls == 2  # only the failed repeats are called again


def test_a_genuinely_empty_answer_is_judged_not_errored(tmp_path):
    root = tmp_path / "p"
    cfg = _api_project(root)
    run_dir, _ = create_api_run(cfg, executor_factory=lambda: FakeExecutor(lambda u: ""))
    js = read_json(judge_run(cfg, run_dir) / "judgments" / "c01" / "1.json")
    assert {j["verdict"] for j in js} == {"FAIL"}


def test_api_receipt_is_labeled_as_emulation_and_verifies(tmp_path):
    root = tmp_path / "p"
    cfg = _api_project(root)
    run_dir, _ = create_api_run(cfg, executor_factory=FakeExecutor)
    judge_run(cfg, run_dir)
    out = build_receipt(cfg)
    r = read_json(out / "receipt.json")
    assert "API EMULATION" in r["flags"] and "emulated" in r["api_note"]
    assert r["executor"]["served_models"] == ["gemini-test-001"] and r["executor"]["calls"] == 20
    assert "executor.v1" in r["prompts"]
    assert r["verdict"] == "VERIFIED", r["reasons"]  # deterministic checks only: no calibration needed
    assert verify_receipt(out / "receipt.json")[0] == []
    assert "emulated" in (out / "receipt.md").read_text()


# --- calibration -----------------------------------------------------------------------------

def _check_of(user):
    return re.search(r"<check>\n(.*?)\n</check>", user, re.S).group(1)


def _output_of(user):
    return re.search(r"<output>\n(.*?)\n</output>", user, re.S).group(1).strip()


def _mixed_judge():
    """PASS on property 1, FAIL on property 2: a judge with both verdicts to calibrate."""
    def responder(user, n):
        verdict = "FAIL" if "number 2" in _check_of(user) else "PASS"
        return {"verdict": verdict, "reason": "r", "evidence": _output_of(user)}
    return FakeModel(responder)


def _pass_judge():
    return FakeModel(lambda user, n: {"verdict": "PASS", "reason": "r", "evidence": _output_of(user)})


def _calibration_project(tmp_path):
    root = tmp_path / "p"
    make_project(root, model_checks=2)
    cfg = _set(root, ["repeats"], 3)
    assign_splits(cfg.paths["cases"], cfg.paths["golden"], 0.3, seed=11)
    ratify(cfg.paths["criteria"], "Dana Expert")
    run_dir, _ = create_manual_run(cfg)
    fill_outputs(run_dir, lambda cid, r: f"OK {cid}\n")
    judge_dir = judge_run(cfg, run_dir, model_factory=_mixed_judge)
    return root, cfg, judge_dir


def _label(sheet_dir, decide):
    items = {it["item_id"]: it for it in read_json(sheet_dir / "items.json")["items"]}
    rows = [{"item_id": i, "human_label": decide(it), "notes": ""} for i, it in items.items()]
    with open(sheet_dir / "labels.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["item_id", "human_label", "notes"])
        w.writeheader()
        w.writerows(rows)
    return sheet_dir / "labels.csv"


def _agree(it):
    return "FAIL" if it["check_id"] == "M2" else "PASS"


def test_export_is_blind_and_stratified(tmp_path):
    _, cfg, judge_dir = _calibration_project(tmp_path)
    sheet = export_sheet(cfg, judge_dir, seed=5)
    items = read_json(sheet / "items.json")
    assert len(items["items"]) == 30
    assert not any("verdict" in it for it in items["items"])
    labels = (sheet / "labels.csv").read_text().splitlines()
    assert labels[0] == "item_id,human_label,notes" and all(line.endswith(",,") for line in labels[1:])
    fails = sum(1 for it in items["items"] if it["check_id"] == "M2")
    assert fails == 15  # half the sample is FAIL verdicts
    for it in items["items"]:  # dev cases only
        case = yaml.safe_load((cfg.paths["cases"] / f"{it['case_id']}.yaml").read_text())
        assert case["split"] == "dev"


def test_calibrated_judge_allows_verified_and_uncalibrated_blocks_it(tmp_path):
    root, cfg, judge_dir = _calibration_project(tmp_path)
    # Before calibration, a model-judged run that passes everything is still NOT VERIFIED.
    run_dir, _ = create_manual_run(cfg)
    fill_outputs(run_dir, lambda cid, r: f"OK {cid}\n")
    judge_run(cfg, run_dir, model_factory=_pass_judge)
    r = read_json(build_receipt(cfg) / "receipt.json")
    assert r["verdict"] == "NOT VERIFIED" and "JUDGE UNCALIBRATED" in r["flags"]

    record = import_labels(cfg, _label(export_sheet(cfg, judge_dir, seed=5), _agree), by="Dana Expert")
    assert read_json(record)["status"] == "CALIBRATED"
    out = build_receipt(cfg, run_dir)
    r = read_json(out / "receipt.json")
    assert r["calibration"]["status"] == "CALIBRATED" and r["verdict"] == "VERIFIED", r["reasons"]
    assert verify_receipt(out / "receipt.json")[0] == []


def test_below_threshold_calibration_keeps_the_judge_uncalibrated(tmp_path):
    root, cfg, judge_dir = _calibration_project(tmp_path)
    sheet = export_sheet(cfg, judge_dir, seed=5)
    flipped = iter(range(100))
    record = import_labels(cfg, _label(sheet, lambda it: ("PASS" if _agree(it) == "FAIL" else "FAIL")
                                       if next(flipped) < 5 else _agree(it)), by="Dana")
    rec = read_json(record)
    assert rec["status"] == "BELOW THRESHOLD" and rec["counts"]["agree"] == 25 and rec["required"]["agree"] == 27
    run_dir, _ = create_manual_run(cfg)
    fill_outputs(run_dir, lambda cid, r: f"OK {cid}\n")
    judge_run(cfg, run_dir, model_factory=_pass_judge)
    r = read_json(build_receipt(cfg) / "receipt.json")
    assert r["calibration"]["status"] == "JUDGE UNCALIBRATED" and r["verdict"] == "NOT VERIFIED"


def test_calibration_is_tied_to_the_judge_model_settings_and_prompt(tmp_path, monkeypatch):
    root, cfg, judge_dir = _calibration_project(tmp_path)
    import_labels(cfg, _label(export_sheet(cfg, judge_dir, seed=5), _agree), by="Dana")
    from skillgate.calibrate import current_identity, find_record

    assert find_record(cfg, current_identity(cfg)) is not None
    cfg2 = _set(root, ["judge", "settings", "effort"], "medium")
    assert find_record(cfg2, current_identity(cfg2)) is None
    cfg3 = _set(root, ["judge", "settings", "effort"], "high")
    alt = tmp_path / "prompts"
    shutil.copytree(prompts_module.PROMPTS_DIR, alt)
    (alt / "judge.v1.md").write_text((alt / "judge.v1.md").read_text() + "\nBe strict.\n")
    monkeypatch.setattr(prompts_module, "PROMPTS_DIR", alt)
    assert find_record(cfg3, current_identity(cfg3)) is None


def test_small_sample_is_refused(tmp_path):
    root = tmp_path / "p"
    make_project(root, model_expectation=True)
    cfg = load_config(root / "skillgate.yaml")
    assign_splits(cfg.paths["cases"], cfg.paths["golden"], 0.3, seed=11)
    ratify(cfg.paths["criteria"], "Dana")
    run_dir, _ = create_manual_run(cfg)
    fill_outputs(run_dir, lambda cid, r: f"OK {cid}\n")
    judge_dir = judge_run(cfg, run_dir, model_factory=_pass_judge)
    with pytest.raises(SkillGateError, match="needs 30 model judgments"):
        export_sheet(cfg, judge_dir)


def test_edited_calibration_label_is_detected(tmp_path):
    root, cfg, judge_dir = _calibration_project(tmp_path)
    record = import_labels(cfg, _label(export_sheet(cfg, judge_dir, seed=5), _agree), by="Dana")
    run_dir, _ = create_manual_run(cfg)
    fill_outputs(run_dir, lambda cid, r: f"OK {cid}\n")
    judge_run(cfg, run_dir, model_factory=_pass_judge)
    out = build_receipt(cfg, run_dir)
    rec = read_json(record)
    rec["items"][0]["human_label"] = "FAIL" if rec["items"][0]["human_label"] == "PASS" else "PASS"
    write_json(record, rec)
    problems, _ = verify_receipt(out / "receipt.json")
    assert any("calibration" in p for p in problems)


# --- staleness -------------------------------------------------------------------------------

def _fresh_receipt(tmp_path):
    root = tmp_path / "p"
    cfg = _api_project(root)
    run_dir, _ = create_api_run(cfg, executor_factory=FakeExecutor)
    judge_run(cfg, run_dir)
    build_receipt(cfg)
    assert check_stale(cfg)[0] == []
    return root, cfg


def test_one_changed_skill_line_is_stale_and_exits_nonzero(tmp_path, capsys, monkeypatch):
    root, _ = _fresh_receipt(tmp_path)
    skill = root / "skill.md"
    skill.write_text(skill.read_text().replace("reply \"EMPTY\"", "reply \"NOTHING\""))
    monkeypatch.chdir(root)
    assert main(["check-stale"]) == 1
    out = capsys.readouterr().out
    assert out.startswith("STALE") and "skill:" in out


@pytest.mark.parametrize("path,value,expect", [
    (["executor", "model"], "gemini-test-002", "executor model: gemini-test-001 → gemini-test-002"),
    (["judge", "model"], "claude-sonnet-5", "judge model: claude-opus-5 → claude-sonnet-5"),
    (["executor", "settings", "temperature"], 0.1, "executor settings changed"),
])
def test_model_changes_are_stale(tmp_path, path, value, expect):
    root, _ = _fresh_receipt(tmp_path)
    cfg = _set(root, path, value)
    assert expect in check_stale(cfg)[0]


def test_reference_and_prompt_changes_are_stale(tmp_path, monkeypatch):
    root, cfg = _fresh_receipt(tmp_path)
    ref = root / "reference.md"
    ref.write_text("# Ref\n\nPolicy.\n")
    cfg = _set(root, ["skill", "references"], ["reference.md"])
    assert "reference added: reference.md" in check_stale(cfg)[0]
    alt = tmp_path / "prompts"
    shutil.copytree(prompts_module.PROMPTS_DIR, alt)
    (alt / "judge.v1.md").write_text((alt / "judge.v1.md").read_text() + "\n")
    monkeypatch.setattr("skillgate.stale.PROMPTS_DIR", alt)
    assert "prompt judge.v1 changed" in check_stale(cfg)[0]


def test_fresh_receipt_exits_zero(tmp_path, capsys, monkeypatch):
    root, _ = _fresh_receipt(tmp_path)
    monkeypatch.chdir(root)
    assert main(["check-stale"]) == 0
    assert capsys.readouterr().out.startswith("FRESH")

import csv

import pytest
import yaml

from skillgate.cases import assign_splits, draw_holdout, golden_stats, load_cases, load_golden, verify_splits
from skillgate.config import DEFAULT_THRESHOLDS, load_config
from skillgate.interview import import_csv
from skillgate.util import SkillGateError


def test_splits_are_seeded_reproducible_and_at_least_30_percent(project):
    cfg = load_config(project / "skillgate.yaml")
    draw = assign_splits(cfg.paths["cases"], cfg.paths["golden"], 0.3, seed=42)
    assert draw["holdout_count"] == 3
    assert draw["holdout"] == draw_holdout(42, draw["pool"], 3)
    cases = load_cases(cfg.paths["cases"])
    assert sum(c.split == "holdout" for c in cases) == 3
    assert verify_splits(cases, load_golden(cfg.paths["golden"])) == []
    assert assign_splits(cfg.paths["cases"], cfg.paths["golden"], 0.3) is None  # nothing new to draw


def test_hand_edited_split_is_detected(project):
    cfg = load_config(project / "skillgate.yaml")
    assign_splits(cfg.paths["cases"], cfg.paths["golden"], 0.3, seed=7)
    victim = next(c for c in load_cases(cfg.paths["cases"]) if c.split == "holdout")
    data = yaml.safe_load(victim.path.read_text())
    data["split"] = "dev"
    victim.path.write_text(yaml.safe_dump(data))
    problems = verify_splits(load_cases(cfg.paths["cases"]), load_golden(cfg.paths["golden"]))
    assert any(victim.id in p for p in problems)


def test_unconfirmed_generated_case_is_refused(project):
    p = project / "golden" / "cases" / "c01.yaml"
    data = yaml.safe_load(p.read_text())
    data.update(source="generated", confirmed_by=None, confirmed_at=None, split="dev")
    p.write_text(yaml.safe_dump(data))
    with pytest.raises(SkillGateError, match="not confirmed"):
        load_cases(project / "golden" / "cases", require_ready=True)


def test_expected_text_is_rejected_as_an_expectation(project):
    p = project / "golden" / "cases" / "c01.yaml"
    data = yaml.safe_load(p.read_text())
    data["expectations"] = ['"OK c01"']
    p.write_text(yaml.safe_dump(data))
    with pytest.raises(SkillGateError, match="binary statement"):
        load_cases(project / "golden" / "cases")


def test_golden_minimums(project):
    cases = load_cases(project / "golden" / "cases")
    stats = golden_stats(cases[:9], DEFAULT_THRESHOLDS)
    assert any("at least 10" in b for b in stats["blockers"])
    assert any("at least 12" in w for w in stats["warnings"])
    few_edge = [c for c in cases if not c.is_edge]  # 6 plain cases
    stats = golden_stats(few_edge, DEFAULT_THRESHOLDS)
    assert any("edge or should_not_flag" in w for w in stats["warnings"])


def _write_csv(path, rows, extra_cols=()):
    cols = ["id", "input_text", "input_files", "expectations", "tags", "source", "confirmed_by", "confirmed_at", *extra_cols]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})


def test_csv_import_writes_cases_and_draws_splits(tmp_path):
    rows = [{"id": f"x{i}", "input_text": f"input {i}",
             "expectations": "detect: Flags the duplicate invoice\nno_flag: Does not flag the credit note",
             "tags": "edge; duplicate" if i < 4 else "plain"} for i in range(10)]
    _write_csv(tmp_path / "cases.csv", rows)
    res = import_csv(tmp_path / "cases.csv", tmp_path / "cases", tmp_path / "golden.yaml", 0.3, seed=1)
    assert len(res["written"]) == 10 and res["draw"]["holdout_count"] == 3
    c = yaml.safe_load((tmp_path / "cases" / "x0.yaml").read_text())
    assert [e["kind"] for e in c["expectations"]] == ["detect", "no_flag"]
    assert c["tags"] == ["edge", "duplicate"] and c["split"] in ("dev", "holdout")
    again = import_csv(tmp_path / "cases.csv", tmp_path / "cases", tmp_path / "golden.yaml", 0.3)
    assert again["unchanged"] and not again["written"]


def test_csv_with_split_column_is_refused(tmp_path):
    _write_csv(tmp_path / "c.csv", [{"id": "a", "input_text": "x", "expectations": "y"}], extra_cols=("split",))
    with pytest.raises(SkillGateError, match="split"):
        import_csv(tmp_path / "c.csv", tmp_path / "cases", tmp_path / "g.yaml", 0.3)


def test_failed_import_writes_nothing(tmp_path):
    _write_csv(tmp_path / "c.csv", [{"id": "ok1", "input_text": "x", "expectations": "y"},
                                    {"id": "bad id!", "input_text": "x", "expectations": "y"}])
    with pytest.raises(SkillGateError):
        import_csv(tmp_path / "c.csv", tmp_path / "cases", tmp_path / "g.yaml", 0.3)
    assert not list((tmp_path / "cases").glob("*.yaml"))

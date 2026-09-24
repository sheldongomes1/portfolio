import pytest
import yaml

from skillgate.cases import load_cases
from skillgate.checks import run_check
from skillgate.criteria import check_ratified, coverage, load_criteria, propose, ratify
from skillgate.skill import extract_rules, load_skill
from skillgate.util import SkillGateError


def test_ratification_is_recorded_and_invalidated_by_edits(project):
    path = project / "golden" / "criteria.yaml"
    with pytest.raises(SkillGateError, match="not been ratified"):
        check_ratified(path)
    with pytest.raises(SkillGateError, match="--by"):
        ratify(path, "")
    rec = ratify(path, "Dana Expert")
    assert check_ratified(path)["ratified_by"] == "Dana Expert" and rec["criteria_sha256"]
    path.write_text(path.read_text() + "\n# a later edit\n")
    with pytest.raises(SkillGateError, match="changed after it was ratified"):
        check_ratified(path)


def test_partial_credit_criterion_is_rejected(tmp_path):
    p = tmp_path / "criteria.yaml"
    p.write_text(yaml.safe_dump({"criteria": [{"id": "C1", "text": "Scores the tone on a 1-5 scale", "traces_to": ["k00000000"]}]}))
    with pytest.raises(SkillGateError, match="partial credit"):
        load_criteria(p)


def test_untraced_criterion_is_rejected(tmp_path):
    p = tmp_path / "criteria.yaml"
    p.write_text(yaml.safe_dump({"criteria": [{"id": "C1", "text": "Cites a line item"}]}))
    with pytest.raises(SkillGateError, match="traces_to"):
        load_criteria(p)


def test_coverage_lists_uncovered_and_dangling(project):
    skill = load_skill(project / "skill.md")
    rules = extract_rules(skill.text)
    crit = load_criteria(project / "golden" / "criteria.yaml")
    crit[0].traces_to.append("kdeadbeef")
    cov = coverage(rules, crit, load_cases(project / "golden" / "cases"))
    assert cov["covered"] == 1 and cov["uncovered"] == len(rules) - 1
    assert any("kdeadbeef" in d for d in cov["dangling_traces"])


def test_skeleton_proposal_has_one_todo_per_rule_and_never_touches_criteria(project):
    skill = load_skill(project / "skill.md")
    rules = extract_rules(skill.text)
    before = (project / "golden" / "criteria.yaml").read_text()
    out = project / "golden" / "criteria.proposed.yaml"
    meta = propose(skill, rules, out, "criteria.yaml", None)
    assert meta["count"] == len(rules)
    assert yaml.safe_load(out.read_text())["criteria"][0]["traces_to"] == [rules[0].key]
    assert (project / "golden" / "criteria.yaml").read_text() == before


@pytest.mark.parametrize("check,output,verdict", [
    ({"type": "regex", "pattern": r"^Decision: DENY"}, "Decision: DENY\nx", "PASS"),
    ({"type": "regex", "pattern": r"^Decision: DENY"}, "Decision: APPROVE", "FAIL"),
    ({"type": "regex", "pattern": r"ESCALATE", "must": "not_match"}, "Decision: APPROVE", "PASS"),
    ({"type": "regex", "pattern": r"ESCALATE", "must": "not_match"}, "Decision: ESCALATE", "FAIL"),
    ({"type": "contains", "text": "inv-1042"}, "Duplicate of INV-1042", "PASS"),
    ({"type": "required_sections", "sections": ["Flags", "Coverage"]}, "## Flags\nx\n## Coverage\ny", "PASS"),
    ({"type": "required_sections", "sections": ["Flags", "Coverage"]}, "## Flags\nx", "FAIL"),
])
def test_deterministic_checks(check, output, verdict):
    assert run_check(check, output, "input")[0] == verdict


def test_verbatim_quotes_whole_input_and_curly_quotes():
    inp = "The vendor has paused all interface development until the contract is signed."
    good = 'Blocked: “the contract is signed” and "paused all interface development".'
    bad = 'Blocked: "paused most interface development".'
    assert run_check({"type": "verbatim_quotes"}, good, inp)[0] == "PASS"
    verdict, reason, _ = run_check({"type": "verbatim_quotes"}, bad, inp)
    assert verdict == "FAIL" and "not in the input" in reason


def test_verbatim_quotes_by_segment_like_portfolio_brief_gate():
    inp = ("intro\n**Program: A**\nThe vendor has paused all interface development.\n"
           "**Program: B**\nWe have slipped the rehearsal by two weeks.\n")
    check = {"type": "verbatim_quotes", "segments": {"split_pattern": r"^\*\*Program:", "id_format": "U{n:02d}",
                                                     "id_pattern": r"U\d{2}"}}
    ok = '| A [U01] | "The vendor has paused all interface development." |'
    wrong_source = '| A [U02] | "The vendor has paused all interface development." |'
    no_id = '"We have slipped the rehearsal by two weeks."'
    assert run_check(check, ok, inp)[0] == "PASS"
    assert run_check(check, wrong_source, inp)[0] == "FAIL"
    assert "no source ID" in run_check(check, no_id, inp)[1]

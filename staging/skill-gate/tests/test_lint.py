from skillgate.lint import deterministic_findings, run_lint
from skillgate.llm import LLMError
from skillgate.skill import Document, load_skill
from tests.conftest import FakeModel

NAIVE = """\
# Invoice checker

Check the invoice against past invoices and flag anything that looks wrong, etc.
Use the pricing template and see rates.xlsx.
Be professional and use appropriate judgment where relevant.
"""


def _skill(tmp_path, text):
    p = tmp_path / "skill.md"
    p.write_text(text)
    return load_skill(p)


def test_naive_skill_gets_every_deterministic_category(tmp_path):
    cats = {f.category for f in deterministic_findings(_skill(tmp_path, NAIVE), [])}
    assert {"vague", "missing_output_format", "missing_bad_input_behavior", "trusts_input",
            "no_examples", "missing_reference"} <= cats


def test_vague_findings_have_line_numbers_and_rewrites(tmp_path):
    fs = [f for f in deterministic_findings(_skill(tmp_path, NAIVE), []) if f.category == "vague"]
    words = {f.message.split('"')[1].lower().rstrip(".") for f in fs}
    assert {"etc", "professional", "appropriate", "where relevant"} <= words
    assert all(f.line in (3, 5) and f.suggestion for f in fs)


def test_provided_reference_is_not_reported(tmp_path):
    skill = _skill(tmp_path, "See rates.xlsx for prices.\n")
    ref = tmp_path / "rates.xlsx"
    ref.write_bytes(b"x")
    doc = Document(path=ref, text="", sha256="0")
    assert not [f for f in deterministic_findings(skill, [doc]) if f.category == "missing_reference"]


def test_model_findings_with_unverifiable_quotes_are_dropped(tmp_path):
    skill = _skill(tmp_path, NAIVE)

    def responder(user, n):
        return {"findings": [
            {"line": 5, "category": "untestable", "severity": "high", "quote": "Be professional",
             "message": "Not observable.", "suggestion": "Name the words to avoid."},
            {"line": 5, "category": "conflicting", "severity": "high", "quote": "text that is not there",
             "message": "Invented.", "suggestion": "n/a"},
        ]}

    report = run_lint(skill, [], tmp_path / "out", FakeModel(responder))
    model = [f for f in report["findings"] if f["source"] == "model"]
    assert [f["category"] for f in model] == ["untestable"]
    assert report["passes"]["model"]["dropped"] == 1
    assert (tmp_path / "out" / "lint_report.md").is_file()


def test_model_error_is_reported_not_raised(tmp_path):
    report = run_lint(_skill(tmp_path, NAIVE), [], tmp_path / "out", FakeModel(lambda u, n: LLMError("boom")))
    assert report["passes"]["model"]["error"] == "boom"

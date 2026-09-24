"""Deterministic checks. They run before any model judge and never return ERROR.

A criterion or expectation with a `check:` block is decided here; everything
else goes to the model judge. Types:

  regex              pattern, must: match | not_match, ignore_case (default true)
  contains           text, must: match | not_match (plain substring, case-insensitive)
  required_sections  sections: [heading or line text, ...] each must start a line
  verbatim_quotes    every double-quoted passage in the output must appear verbatim in the
                     case input (whitespace collapsed, curly quotes straightened). Optional
                     `segments` maps source IDs to parts of the input, as in Portfolio Brief
                     Gate, where a quote must come from the update whose ID is on its line.
"""

from __future__ import annotations

import re
from typing import Any

from skillgate.util import SkillGateError, normalize_for_match

TYPES = ("regex", "contains", "required_sections", "verbatim_quotes")


def validate_check(check: Any, where: str) -> None:
    if not isinstance(check, dict) or check.get("type") not in TYPES:
        raise SkillGateError(f"{where}: check.type must be one of {', '.join(TYPES)}")
    t = check["type"]
    if check.get("must", "match") not in ("match", "not_match"):
        raise SkillGateError(f"{where}: check.must must be match or not_match")
    if t == "regex":
        try:
            re.compile(str(check.get("pattern", "")))
        except re.error as e:
            raise SkillGateError(f"{where}: invalid regex ({e})") from e
        if not check.get("pattern"):
            raise SkillGateError(f"{where}: regex check needs a pattern")
    elif t == "contains" and not check.get("text"):
        raise SkillGateError(f"{where}: contains check needs text")
    elif t == "required_sections" and not check.get("sections"):
        raise SkillGateError(f"{where}: required_sections check needs sections")
    elif t == "verbatim_quotes":
        seg = check.get("segments")
        if seg is not None and not (isinstance(seg, dict) and seg.get("split_pattern") and seg.get("id_format")):
            raise SkillGateError(f"{where}: verbatim_quotes segments need split_pattern and id_format")


def _excerpt(text: str, n: int = 160) -> str:
    text = text.strip()
    return text if len(text) <= n else text[: n - 1] + "…"


def run_check(check: dict[str, Any], output: str, case_input: str) -> tuple[str, str, str]:
    """Return (verdict, reason, evidence). Verdict is PASS or FAIL."""
    t = check["type"]
    must = check.get("must", "match")
    if t in ("regex", "contains"):
        if t == "regex":
            flags = re.M | (re.I if check.get("ignore_case", True) else 0)
            m = re.search(check["pattern"], output, flags)
            found = m.group(0) if m else None
            what = f"/{check['pattern']}/"
        else:
            idx = output.lower().find(str(check["text"]).lower())
            found = output[idx: idx + len(check["text"])] if idx >= 0 else None
            what = f'"{check["text"]}"'
        if must == "match":
            if found is not None:
                return "PASS", f"Output matches {what}.", _excerpt(found)
            return "FAIL", f"Output does not match {what}.", ""
        if found is None:
            return "PASS", f"Output does not match {what}, as required.", ""
        return "FAIL", f"Output matches {what}, which it must not.", _excerpt(found)

    if t == "required_sections":
        missing = []
        for section in check["sections"]:
            pattern = r"^\s*(#+\s*|\*\*)?" + re.escape(str(section))
            if not re.search(pattern, output, re.M | re.I):
                missing.append(str(section))
        if missing:
            return "FAIL", "Missing section(s): " + ", ".join(missing) + ".", ""
        return "PASS", f"All {len(check['sections'])} required section(s) present.", ""

    return _verbatim_quotes(check, output, case_input)


_QUOTE_RE = re.compile(r'"([^"\n]+)"|“([^”\n]+)”')


def _segments(case_input: str, spec: dict[str, Any]) -> dict[str, str]:
    parts = re.split(spec["split_pattern"], case_input, flags=re.M)
    # re.split keeps the text before the first match as parts[0]; segments start after it.
    return {spec["id_format"].format(n=i): normalize_for_match(p) for i, p in enumerate(parts[1:], 1)}


def _verbatim_quotes(check: dict[str, Any], output: str, case_input: str) -> tuple[str, str, str]:
    min_len = int(check.get("min_length", 12))
    spec = check.get("segments")
    whole = normalize_for_match(case_input)
    segs = _segments(case_input, spec) if spec else {}
    id_re = re.compile(spec["id_pattern"]) if spec and spec.get("id_pattern") else None
    checked, bad = 0, []
    for line in output.splitlines():
        for m in _QUOTE_RE.finditer(line):
            quote = m.group(1) or m.group(2)
            if len(quote.strip()) < min_len:
                continue
            checked += 1
            q = normalize_for_match(quote)
            if spec:
                ids = id_re.findall(line) if id_re else []
                if not ids:
                    if check.get("require_id", True):
                        bad.append((quote, "no source ID on its line"))
                    elif q not in whole:
                        bad.append((quote, "not in the input"))
                    continue
                if not any(q in segs.get(i, "") for i in ids):
                    bad.append((quote, f"not in {', '.join(sorted(set(ids)))}"))
            elif q not in whole:
                bad.append((quote, "not in the input"))
    if bad:
        detail = "; ".join(f'"{_excerpt(q, 70)}" ({why})' for q, why in bad[:3])
        more = f" and {len(bad) - 3} more" if len(bad) > 3 else ""
        return "FAIL", f"{len(bad)} of {checked} quote(s) are not verbatim: {detail}{more}.", _excerpt(bad[0][0])
    return "PASS", f"{checked} quote(s) checked; all verbatim.", ""

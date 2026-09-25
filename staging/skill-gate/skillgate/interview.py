"""`skillgate interview --import cases.csv`: golden cases from a spreadsheet export.

For experts who will not use a terminal. The Skill Gate skill (skill/SKILL.md)
produces this file from a conversation. Columns:

  id            required; letters, digits, '.', '_' or '-'
  input_text    the message given to the skill (may be empty if input_files is set)
  input_files   paths relative to the project root, separated by ';'
  expectations  one binary statement per line; a line may start with
                'detect:', 'no_flag:' or 'other:' to set its kind (default other)
  tags          separated by ';' or ','
  source        expert (default) or generated
  confirmed_by, confirmed_at, notes

There is deliberately no split column: splits are drawn at random with a
recorded seed after import.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

from skillgate.cases import ID_RE, _parse_case, assign_splits
from skillgate.util import SkillGateError, dump_yaml, read_yaml

REQUIRED = ("id", "expectations")


def _expectations(cell: str) -> list[dict[str, Any]]:
    out = []
    for line in (cell or "").splitlines():
        line = line.strip().lstrip("-•* ").strip()
        if not line:
            continue
        kind = "other"
        m = re.match(r"^(detect|no_flag|other)\s*:\s*(.+)$", line, re.I)
        if m:
            kind, line = m.group(1).lower(), m.group(2).strip()
        out.append({"id": f"E{len(out) + 1}", "text": line, "kind": kind})
    return out


def import_csv(csv_path: Path, cases_dir: Path, golden_path: Path, share: float, seed: int | None = None) -> dict[str, Any]:
    csv_path = Path(csv_path)
    if not csv_path.is_file():
        raise SkillGateError(f"CSV not found: {csv_path}")
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        columns = [c.strip().lower() for c in reader.fieldnames or []]
        rows = [{(k or "").strip().lower(): (v or "") for k, v in row.items()} for row in reader]
    if "split" in columns:
        raise SkillGateError(
            "The CSV has a 'split' column. Splits are drawn at random by Skill Gate with a recorded "
            "seed, so the author cannot choose the holdout. Remove the column and import again."
        )
    missing = [c for c in REQUIRED if c not in columns]
    if missing:
        raise SkillGateError(f"CSV is missing column(s): {', '.join(missing)}")

    cases_dir = Path(cases_dir)
    cases_dir.mkdir(parents=True, exist_ok=True)
    written, unchanged, errors = [], [], []
    seen: set[str] = set()
    for n, row in enumerate(rows, 2):
        cid = row.get("id", "").strip()
        if not ID_RE.match(cid):
            errors.append(f"row {n}: invalid id '{cid}'")
            continue
        if cid in seen:
            errors.append(f"row {n}: duplicate id '{cid}'")
            continue
        seen.add(cid)
        data: dict[str, Any] = {
            "id": cid,
            "input": {
                "text": row.get("input_text", ""),
                "files": [p.strip() for p in row.get("input_files", "").split(";") if p.strip()],
            },
            "expectations": _expectations(row.get("expectations", "")),
            "tags": [t.strip() for t in re.split(r"[;,]", row.get("tags", "")) if t.strip()],
            "split": None,
            "source": (row.get("source") or "expert").strip().lower(),
            "confirmed_by": row.get("confirmed_by", "").strip() or None,
            "confirmed_at": row.get("confirmed_at", "").strip() or None,
        }
        if row.get("notes", "").strip():
            data["notes"] = row["notes"].strip()
        path = cases_dir / f"{cid}.yaml"
        try:
            _parse_case(path, data)
        except SkillGateError as e:
            errors.append(f"row {n}: {str(e).split(': ', 1)[-1]}")
            continue
        if path.exists():
            existing = read_yaml(path) or {}
            comparable = {k: v for k, v in existing.items() if k != "split"}
            if comparable == {k: v for k, v in data.items() if k != "split"}:
                unchanged.append(cid)
                continue
            errors.append(f"row {n}: {path.name} already exists with different content; not overwritten")
            continue
        path.write_text(dump_yaml(data), encoding="utf-8")
        written.append(cid)
    if errors:
        # Roll back files written in this import so a failed import leaves nothing half-done.
        for cid in written:
            (cases_dir / f"{cid}.yaml").unlink()
        raise SkillGateError("Import failed; nothing was written:\n  " + "\n  ".join(errors))
    draw = assign_splits(cases_dir, golden_path, share, seed)
    return {"written": written, "unchanged": unchanged, "draw": draw}

"""Hashing, time stamps, text normalization and file I/O shared by every command."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


class SkillGateError(Exception):
    """An error the user can fix. The CLI prints it without a traceback."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def stamp(dt: datetime) -> str:
    """A sortable, filesystem-safe UTC time stamp: 20260924T221500Z."""
    return dt.strftime("%Y%m%dT%H%M%SZ")


_CURLY = str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'"})


def squash(text: str) -> str:
    """Collapse whitespace runs, as the Portfolio Brief Gate quote validator does."""
    return re.sub(r"\s+", " ", text).strip()


def normalize_for_match(text: str) -> str:
    """Whitespace collapsed and curly quotes straightened. Nothing else is forgiven."""
    return squash(text.translate(_CURLY))


def rel(path: Path, root: Path) -> str:
    return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()


def read_yaml(path: Path) -> Any:
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise SkillGateError(f"{path}: not valid YAML ({e})") from e


def dump_yaml(data: Any) -> str:
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=100)


def write_json(path: Path, data: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(canonical_json(data, indent=2) + "\n", encoding="utf-8")


def canonical_json(data: Any, indent: int | None = None) -> str:
    return json.dumps(data, sort_keys=True, indent=indent, ensure_ascii=False)


def read_json(path: Path) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def new_dir(path: Path) -> Path:
    """Create a directory that must not exist yet. Runs and receipts are never overwritten."""
    path = Path(path)
    if path.exists():
        raise SkillGateError(f"{path} already exists; Skill Gate never overwrites a run or receipt")
    path.mkdir(parents=True)
    return path

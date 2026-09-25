"""Executor output cache, so re-running unchanged work costs nothing.

The key covers everything that can change an output: the skill's hash, every
reference file's hash, the case file's and its input files' hashes, the
executor model ID, its settings, the prompt-assembly hash, and the repeat
index. Only completed outputs are cached, never failures.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from skillgate.util import canonical_json, read_json, sha256_text, write_json


def cache_key(**parts: Any) -> str:
    return sha256_text(canonical_json(parts))


class Cache:
    def __init__(self, directory: Path):
        self.dir = Path(directory) / "executor"

    def get(self, key: str) -> dict[str, Any] | None:
        p = self.dir / f"{key}.json"
        return read_json(p) if p.is_file() else None

    def put(self, key: str, entry: dict[str, Any]) -> None:
        write_json(self.dir / f"{key}.json", entry)

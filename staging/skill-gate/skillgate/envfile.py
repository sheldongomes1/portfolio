"""Load API keys from a local `.env` file, so they need not be exported by hand.

Skill Gate looks for `.env` in the current directory, then in each parent up to
and including the repository root (the first directory holding `.git`). The
first file found is read. Lines are `NAME=value` (an `export ` prefix and
surrounding quotes are allowed); blank lines and `#` comments are ignored.

Variables already set in the environment always win, and empty values are
skipped, so a blank template never hides a key exported in the shell. Values
are never printed.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

_LINE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$")


def find_env_file(start: Path) -> Path | None:
    d = Path(start).resolve()
    while True:
        if (d / ".env").is_file():
            return d / ".env"
        if (d / ".git").exists() or d.parent == d:
            return None
        d = d.parent


def parse(text: str) -> dict[str, str]:
    values = {}
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = _LINE.match(line)
        if not m:
            continue
        name, value = m.groups()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        else:
            value = re.sub(r"\s+#.*$", "", value)
        values[name] = value
    return values


def load_env_file(start: Path | None = None) -> Path | None:
    """Set unset variables from the nearest `.env`. Returns the file read, if any."""
    path = find_env_file(Path.cwd() if start is None else start)
    if path is None:
        return None
    for name, value in parse(path.read_text(encoding="utf-8")).items():
        if value and not os.environ.get(name):
            os.environ[name] = value
    return path

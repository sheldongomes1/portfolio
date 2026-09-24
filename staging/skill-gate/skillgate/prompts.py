"""Versioned prompt files in prompts/. Their SHA-256 goes into every receipt."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from skillgate.util import SkillGateError, sha256_file

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


@dataclass
class Prompt:
    name: str
    path: Path
    sha256: str
    system: str
    user: str

    def render(self, **values: str) -> tuple[str, str]:
        def fill(template: str) -> str:
            out = template
            for key, value in values.items():
                out = out.replace("{{" + key + "}}", value)
            left = re.findall(r"\{\{[A-Z_]+\}\}", out)
            if left:
                raise SkillGateError(f"prompt {self.name}: no value for {', '.join(sorted(set(left)))}")
            return out

        return fill(self.system), fill(self.user)


def load_prompt(name: str) -> Prompt:
    path = PROMPTS_DIR / f"{name}.md"
    if not path.is_file():
        raise SkillGateError(f"Prompt file not found: {path}")
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^=== system ===\n(.*?)^=== user ===\n(.*)\Z", text, re.S | re.M)
    if not m:
        raise SkillGateError(f"{path}: expected '=== system ===' and '=== user ===' sections")
    return Prompt(name=name, path=path, sha256=sha256_file(path), system=m.group(1).strip(), user=m.group(2).strip())

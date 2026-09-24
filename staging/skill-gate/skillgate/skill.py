"""Loading a skill and its reference files, and extracting the rules a skill states.

A skill arrives as Markdown, plain text, or a .docx export of the Google Doc it
was written in. Rules are extracted deterministically so coverage can be
computed without a model: list items, table body rows, and sentences that use
rule language (must, never, always, do not, only, ...). Each rule gets a key
derived from its normalized text, so reordering the skill keeps the key and
rewording a rule changes it.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path

from skillgate.util import SkillGateError, sha256_file, sha256_text, squash

_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


@dataclass
class Document:
    path: Path
    text: str
    sha256: str

    @property
    def lines(self) -> list[str]:
        return self.text.splitlines()

    @property
    def title(self) -> str:
        for line in self.lines:
            m = re.match(r"^\s*#\s+(.+?)\s*$", line)
            if m:
                return m.group(1)
        return self.path.stem


@dataclass
class Skill(Document):
    name: str
    version: str | None


@dataclass
class Rule:
    index: int
    key: str
    line: int
    text: str

    @property
    def label(self) -> str:
        return f"R{self.index:02d}"


def read_text(path: Path) -> str:
    path = Path(path)
    if not path.is_file():
        raise SkillGateError(f"File not found: {path}")
    if path.suffix.lower() == ".docx":
        return _docx_text(path)
    if path.suffix.lower() not in {".md", ".markdown", ".txt"}:
        raise SkillGateError(f"{path}: expected .md, .txt or .docx")
    return path.read_text(encoding="utf-8")


def _docx_text(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml")
    except (zipfile.BadZipFile, KeyError) as e:
        raise SkillGateError(f"{path}: not a readable .docx file ({e})") from e
    root = ET.fromstring(xml)
    paragraphs = []
    for p in root.iter(f"{_W}p"):
        parts = []
        for node in p.iter():
            if node.tag == f"{_W}t" and node.text:
                parts.append(node.text)
            elif node.tag == f"{_W}tab":
                parts.append("\t")
        paragraphs.append("".join(parts))
    return "\n".join(paragraphs) + "\n"


def load_document(path: Path) -> Document:
    return Document(path=Path(path), text=read_text(path), sha256=sha256_file(path))


def load_skill(path: Path, name: str | None = None) -> Skill:
    doc = load_document(path)
    version = None
    front_name = None
    lines = doc.lines
    if lines and lines[0].strip() == "---":
        for line in lines[1:40]:
            if line.strip() == "---":
                break
            m = re.match(r"^\s*(name|version)\s*:\s*(.+?)\s*$", line)
            if m and m.group(1) == "name":
                front_name = m.group(2).strip("'\"")
            elif m:
                version = m.group(2).strip("'\"")
    if version is None:
        for line in lines[:5]:
            m = re.match(r"^\s*\**\s*Version\s*\**\s*:\s*\**\s*v?([0-9][\w.\-]*)", line, re.I)
            if m:
                version = m.group(1)
                break
    return Skill(
        path=doc.path,
        text=doc.text,
        sha256=doc.sha256,
        name=name or front_name or doc.path.parent.name or doc.path.stem,
        version=version,
    )


RULE_WORDS = re.compile(
    r"\b(must|never|always|do not|don't|does not|only|should|required?|refuse|reject|"
    r"flag|ignore|stop|cite|quote|include|exclude|every|each|exactly|reply|respond|apply|no\b)",
    re.I,
)


def _clean(text: str) -> str:
    text = re.sub(r"[*_`]+", "", text)
    return squash(text)


def rule_key(text: str) -> str:
    """A stable key for a rule's wording. The k prefix keeps YAML from reading it as a number."""
    return "k" + sha256_text(_clean(text).lower())[:8]


def extract_rules(text: str) -> list[Rule]:
    lines = text.splitlines()
    found: list[tuple[int, str]] = []
    i = 0
    in_fence = False
    in_front = bool(lines) and lines[0].strip() == "---"
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if in_front:
            if i > 0 and stripped == "---":
                in_front = False
            i += 1
            continue
        if stripped.startswith("```"):
            in_fence = not in_fence
            i += 1
            continue
        if in_fence or not stripped or stripped.startswith("#"):
            i += 1
            continue
        item = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", line)
        if item:
            body = [item.group(3)]
            j = i + 1
            while j < len(lines) and lines[j].strip() and lines[j].startswith(" ") and not re.match(
                r"^\s*([-*+]|\d+[.)])\s+", lines[j]
            ):
                body.append(lines[j].strip())
                j += 1
            found.append((i + 1, " ".join(body)))
            i = j
            continue
        if stripped.startswith("|"):
            is_sep = re.match(r"^\|?\s*:?-{2,}", stripped)
            next_is_sep = i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-{2,}", lines[i + 1].strip())
            if not is_sep and not next_is_sep:
                cells = [c.strip() for c in stripped.strip("|").split("|")]
                found.append((i + 1, " | ".join(c for c in cells if c)))
            i += 1
            continue
        # A paragraph: gather it and keep the sentences that use rule language.
        start = i
        para = []
        while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith(("#", "|", "```")) and not re.match(
            r"^\s*([-*+]|\d+[.)])\s+", lines[i]
        ):
            para.append(lines[i].strip())
            i += 1
        for sentence in re.split(r"(?<=[.!?])\s+", " ".join(para)):
            if RULE_WORDS.search(sentence):
                found.append((start + 1, sentence))

    rules: list[Rule] = []
    seen: set[str] = set()
    for line_no, raw in found:
        cleaned = _clean(raw)
        if len(cleaned) < 8:
            continue
        key = rule_key(cleaned)
        if key in seen:
            continue
        seen.add(key)
        rules.append(Rule(index=len(rules) + 1, key=key, line=line_no, text=cleaned))
    return rules

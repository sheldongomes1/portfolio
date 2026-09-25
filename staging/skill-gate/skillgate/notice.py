"""The data-handling notice (PRD 5.5), printed before any step that sends data out.

The first time a project sends anything to an external model API, the user
must confirm. The confirmation is stored in .skillgate/state.json in the
project (git-ignored). Non-interactive use passes --yes.
"""

from __future__ import annotations

import sys
from pathlib import Path

from skillgate.util import SkillGateError, iso, read_json, utc_now, write_json

NOTICE = """\
DATA HANDLING: this step sends {what} to {provider}'s API.
Use fictional data, or data whose owner has approved sending it to that provider.
Do not run Skill Gate on confidential material without that approval."""


def ensure_accepted(root: Path, what: str, provider: str, assume_yes: bool = False) -> None:
    print(NOTICE.format(what=what, provider=provider), file=sys.stderr)
    state_path = Path(root) / ".skillgate" / "state.json"
    state = read_json(state_path) if state_path.is_file() else {}
    if state.get("data_notice_accepted_at"):
        return
    if not assume_yes:
        if not sys.stdin.isatty():
            raise SkillGateError(
                "First use in this project: confirm the data-handling notice above by running "
                "the command again with --yes."
            )
        answer = input("Type 'yes' to confirm and continue: ").strip().lower()
        if answer != "yes":
            raise SkillGateError("Not confirmed; nothing was sent.")
    state["data_notice_accepted_at"] = iso(utc_now())
    write_json(state_path, state)

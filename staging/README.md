# staging/

Work in progress for two other repositories, built here because this is where the build
session can push. Nothing in this folder is part of the website: the `Dockerfile` copies an
explicit list of files, and `staging/` is not on it.

| Folder here | Destination | Contents |
|---|---|---|
| `portfolio-brief-gate/workspace/` | `workspace/` in [portfolio-brief-gate](https://github.com/sheldongomes1/portfolio-brief-gate) | Portfolio Brief Gate, Google Workspace edition (PRD deliverable D1) |
| `skill-gate/` | a new `skill-gate` repository | Skill Gate CLI, skill, spec and demo (D2–D5). Milestones 2 and 3 done: the core CLI, API mode, cost caps, calibration, staleness checks, CI, tests and a key-free example |

Moving a folder to its destination is a copy. For `skill-gate/`, running
`git subtree split --prefix=staging/skill-gate` keeps its history.

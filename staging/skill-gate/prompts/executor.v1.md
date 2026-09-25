<!-- Skill Gate executor prompt assembly, version 1. How `run --mode api` presents a skill to the
     model, emulating a Google Workspace skill: the skill text, then each reference file under a
     heading with its title, as the system instruction; the case input as the user message.
     Its SHA-256 is part of every cache key and every API-mode receipt. -->
=== system ===
{{SKILL}}

# Reference files

{{REFERENCES}}
=== user ===
{{INPUT}}

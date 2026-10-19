#!/usr/bin/env python3
"""Link the skill folders of this clone into ~/.agents/skills/.

Codex and Gemini CLI read skills from ~/.agents/skills/. Each folder in
plugins/*/skills/ gets one link there. A git pull in the clone then updates
every tool.

On Windows the link is a directory junction, which needs no admin rights.
Elsewhere it is a symlink.

The script never replaces an entry that is not already a link to this clone.
It reports each link as made, present or skipped, and exits 1 if it skipped one.
"""

import os
import subprocess
import sys
from pathlib import Path

CLONE = Path(__file__).resolve().parent.parent
TARGET_DIR = Path.home() / ".agents" / "skills"


def skill_folders():
    """Return every skill folder of the clone, sorted by name."""
    return sorted(p for p in CLONE.glob("plugins/*/skills/*") if (p / "SKILL.md").is_file())


def make_link(link, source):
    """Link `link` to the folder `source`: a junction on Windows, else a symlink."""
    if os.name == "nt":
        result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(source)],
                                capture_output=True, text=True)
        if result.returncode != 0:
            raise OSError(result.stderr.strip() or result.stdout.strip())
    else:
        os.symlink(source, link, target_is_directory=True)


def link_skill(source):
    """Link one skill folder. Return (state, detail)."""
    link = TARGET_DIR / source.name
    if os.path.lexists(link):
        if os.path.realpath(link) == os.path.realpath(source):
            return "present", str(link)
        return "skipped", f"{link} exists and is not a link to this clone"
    make_link(link, source)
    return "made", f"{link} -> {source}"


def main():
    skills = skill_folders()
    if not skills:
        print(f"error: no skill folders in {CLONE / 'plugins'}", file=sys.stderr)
        return 1
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    skipped = 0
    for source in skills:
        try:
            state, detail = link_skill(source)
        except OSError as e:
            state, detail = "skipped", f"{TARGET_DIR / source.name}: {e}"
        if state == "skipped":
            skipped += 1
        print(f"{state:8} {source.name}: {detail}")
    return 1 if skipped else 0


if __name__ == "__main__":
    sys.exit(main())

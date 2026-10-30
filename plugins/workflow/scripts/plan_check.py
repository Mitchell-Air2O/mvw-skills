#!/usr/bin/env python3
"""Print each Checked: block of a plan that names no command and no file:line.

Usage:
    plan_check.py PLAN_PATH

A block starts at a line that begins with "Checked:" and ends at the next
blank line. It passes when it names a command (grep, git, pio or python) or a
file and line. The script exits with 1 when it prints a block.

The script checks the form only. A block with a command can still hold a stale
value, so the planner runs the command again when a value changes.
"""

import argparse
import re
import sys

CHECKED_RE = re.compile(r"^\s*(?:[-*] )?\**Checked:")
EVIDENCE_RE = re.compile(r"\b(grep|git|pio|python)\b|\.\w+:\d+")


def checked_blocks(lines):
    """Yield (line number, text) for each Checked: block."""
    start = None
    block = []
    for number, line in enumerate(lines, 1):
        if not line.strip():
            if start:
                yield start, "\n".join(block)
            start = None
            block = []
        elif start or CHECKED_RE.match(line):
            start = start or number
            block.append(line.rstrip())
    if start:
        yield start, "\n".join(block)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("plan_path")
    args = parser.parse_args()
    try:
        with open(args.plan_path, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError as error:
        sys.exit(f"error: {error}")
    sys.stdout.reconfigure(encoding="utf-8")
    failed = 0
    for number, text in checked_blocks(lines):
        if not EVIDENCE_RE.search(text):
            print(f"{args.plan_path}:{number}: no command and no file:line\n{text}\n")
            failed += 1
    print(f"{failed} block(s) without evidence")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

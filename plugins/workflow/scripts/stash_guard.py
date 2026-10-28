#!/usr/bin/env python3
"""Refuse a git stash command that can take another session's changes.

A PreToolUse hook for the Bash and PowerShell tools (hooks/hooks.json). Every
worktree of a repository shares one stash stack, and other sessions push to it
and apply from it at the same time. So this hook refuses each stash command
that acts on an entry it does not name:
- a stash with no message: "git stash", "git stash -q", "git stash push";
- "git stash save", which git deprecates; use "git stash push -m";
- "git stash pop", because it removes an entry by its place in the stack;
- "git stash apply" and "git stash drop" with no entry named;
- "git stash clear".

It allows "git stash push -m <tag>", "apply <sha>", "drop stash@{n}", "list",
"show" and the other subcommands.

Claude Code sends the tool call as JSON on stdin. Exit code 2 refuses the call,
and the agent reads the text on stderr. Input that is not JSON passes, so a
change of the input format never blocks a command.

Stdlib only.
"""

import json
import re
import shlex
import sys

# "git" at the start of a command, its global options ("-C <path>",
# "--no-pager"), then "stash" and its arguments up to the next shell separator.
# The start of a command keeps a quoted "git stash" in a grep or a message out.
STASH_RE = re.compile(r"(?:^|[;&|(\n`]|\$\()\s*git"
                      r"((?:\s+-[Cc]\s+\S+|\s+--?[\w-]+(?:=\S+)?)*)"
                      r"\s+stash\b([^;&|\n)`]*)")

ADVICE = (
    "Every worktree and session shares one stash stack, so this command can "
    "take another session's changes. To set work aside, make a WIP commit, or "
    "run `git stash push -u -m <unique tag>`. Find its SHA with "
    "`git stash list --format='%H %gs'`, restore it with `git stash apply "
    "<sha>`, then drop it by its current stash@{n}. To test an old tree, "
    "export it: `git archive <rev> | tar -x -C <scratch dir>`, or "
    "`git worktree add --detach <scratch dir> <rev>`.")


def words(text):
    try:
        return shlex.split(text)
    except ValueError:
        return text.split()


def has_message(args):
    return any(a == "--message" or a.startswith("--message=")
               or (a.startswith("-m") and not a.startswith("--"))
               for a in args)


def refusal(args):
    """The reason to refuse one stash command, or None to allow it."""
    if not args or args[0].startswith("-"):
        sub, rest = "push", args
    else:
        sub, rest = args[0], args[1:]
    named = [a for a in rest if not a.startswith("-")]
    if sub == "push" and not has_message(rest):
        return "a stash with no message"
    if sub == "save":
        return "git stash save; use git stash push -m <tag>"
    if sub == "pop":
        return "git stash pop"
    if sub == "clear":
        return "git stash clear"
    if sub in ("apply", "drop") and not named:
        return "git stash %s with no entry named" % sub
    return None


def check(command):
    """The reasons to refuse the stash commands in one shell command."""
    return [r for r in (refusal(words(m.group(2)))
                        for m in STASH_RE.finditer(command)) if r]


def main():
    try:
        call = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(call, dict):
        return 0
    command = str((call.get("tool_input") or {}).get("command") or "")
    reasons = check(command)
    if reasons:
        print("Refused: %s (stash_guard.py). %s" % ("; ".join(reasons), ADVICE),
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

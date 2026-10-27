#!/usr/bin/env python3
"""Apply the builder's edits to a plan file, all or none.

Usage:
    plan_update.py PLAN [--replace OLD NEW]... [--append HEADING TEXT]...
                        [--next-step TEXT]

A worktree session cannot use Edit on a plan in the main checkout, because
a hook refuses it. This script makes the same edits through Bash:

--replace OLD NEW   Replace the text OLD with NEW. OLD must occur exactly
                    one time. Use it for a stage row or a status line.
--append HEADING TEXT
                    Add TEXT at the end of the section under the heading
                    line HEADING (for example "## Stage results"), before
                    the next heading of the same or a higher level. The
                    heading must occur exactly one time. TEXT goes right
                    after the last line of the section, so a list item
                    joins the list. Start TEXT with a blank line to begin
                    a new paragraph.
--next-step TEXT    Replace the paragraph that starts with
                    "**Next step:**" by "**Next step:** TEXT". The plan
                    must hold exactly one such paragraph.

A TEXT, OLD or NEW that starts with @ is read from the file that follows
the @, so a multi-line block needs no shell quoting. The edits apply in
the order given. If one edit fails, the script names it, writes nothing
and exits 1. A plan with CRLF line endings keeps them.
"""

import argparse
import os
import re
import sys
import tempfile


class EditError(Exception):
    pass


def arg_text(value):
    """Return the value, or the content of the file that @path names."""
    if value.startswith("@"):
        with open(value[1:], encoding="utf-8") as f:
            return f.read()
    return value


def replace_once(text, old, new):
    n = text.count(old)
    if n != 1:
        raise EditError(f"--replace: the text occurs {n} times, not 1: {old[:60]!r}")
    return text.replace(old, new)


def append_to_section(text, heading, block):
    lines = text.split("\n")
    hits = [i for i, l in enumerate(lines) if l.rstrip() == heading.rstrip()]
    if len(hits) != 1:
        raise EditError(f"--append: the heading occurs {len(hits)} times, not 1: {heading!r}")
    level = len(heading) - len(heading.lstrip("#"))
    if level == 0:
        raise EditError(f"--append: not a Markdown heading: {heading!r}")
    end = len(lines)
    for i in range(hits[0] + 1, len(lines)):
        m = re.match(r"(#+)\s", lines[i])
        if m and len(m.group(1)) <= level:
            end = i
            break
    # The block goes right after the section's last line that is not blank,
    # and one blank line stays before the next heading.
    while end > hits[0] + 1 and lines[end - 1].strip() == "":
        end -= 1
    new = block.rstrip("\n").split("\n")
    tail = [""] if end < len(lines) else []
    rest = lines[end:]
    while rest and rest[0].strip() == "":
        rest = rest[1:]
    return "\n".join(lines[:end] + new + tail + rest)


def set_next_step(text, step):
    pattern = re.compile(r"^\*\*Next step:?\*\*:?.*?(?=\n\s*\n|\Z)", re.M | re.S)
    hits = pattern.findall(text)
    if len(hits) != 1:
        raise EditError(f"--next-step: {len(hits)} paragraphs start with **Next step:**, not 1")
    return pattern.sub(lambda _: "**Next step:** " + step.strip(), text)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("plan")
    parser.add_argument("--replace", nargs=2, action="append", default=[],
                        metavar=("OLD", "NEW"))
    parser.add_argument("--append", nargs=2, action="append", default=[],
                        metavar=("HEADING", "TEXT"))
    parser.add_argument("--next-step", metavar="TEXT")
    args = parser.parse_args()

    with open(args.plan, "rb") as f:
        raw = f.read().decode("utf-8")
    crlf = "\r\n" in raw
    text = raw.replace("\r\n", "\n")

    try:
        for old, new in args.replace:
            text = replace_once(text, arg_text(old).replace("\r\n", "\n"),
                                arg_text(new).replace("\r\n", "\n"))
        for heading, block in args.append:
            text = append_to_section(text, heading, arg_text(block).replace("\r\n", "\n"))
        if args.next_step is not None:
            text = set_next_step(text, arg_text(args.next_step))
    except (EditError, OSError) as e:
        print(f"plan_update.py: {e}. Nothing written.", file=sys.stderr)
        return 1

    if crlf:
        text = text.replace("\n", "\r\n")
    folder = os.path.dirname(os.path.abspath(args.plan))
    fd, tmp = tempfile.mkstemp(dir=folder, suffix=".tmp")
    with os.fdopen(fd, "wb") as f:
        f.write(text.encode("utf-8"))
    os.replace(tmp, args.plan)
    edits = len(args.replace) + len(args.append) + (args.next_step is not None)
    print(f"plan_update.py: {edits} edit(s) written to {args.plan}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

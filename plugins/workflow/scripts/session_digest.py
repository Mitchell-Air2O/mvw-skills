#!/usr/bin/env python3
"""Print a digest of Claude Code sessions for the reviewer's retro.

Usage:
    session_digest.py [--projects-dir DIR] [--target TOKENS] SESSION_ID...

The script finds each session's transcript in the projects folder
(default ~/.claude/projects). A session that moved between worktrees has a
copy in each worktree's folder. Each copy is a snapshot, so the script uses
the largest copy.

For each session, the digest gives:
- the counts: owner messages, requests, compactions, API errors;
- the session's context at its first, largest and last request;
- the tool calls by tool, and the largest tool results;
- one row per subagent: type, description, model, requests, tool calls,
  context at the first and last request, and the messages that the session
  sent to it.

Context is the input tokens of one request: input_tokens plus
cache_read_input_tokens plus cache_creation_input_tokens. context_report.py
uses the same definition. An implementer whose last context is above the
target is marked "over". The target applies only to implementers.
"""

import argparse
import collections
import json
import os
import sys

LARGEST_RESULTS = 5
HINT_LENGTH = 60


def context_of(usage):
    """Return the input tokens of one request from its usage block."""
    return (usage.get("input_tokens", 0)
            + usage.get("cache_read_input_tokens", 0)
            + usage.get("cache_creation_input_tokens", 0))


def kilo(tokens):
    return f"{round(tokens / 1000)}k"


def read_entries(path):
    """Yield the JSON entries of one transcript file. Skip bad lines."""
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                yield json.loads(line)
            except ValueError:
                continue


def find_transcripts(projects_dir, session_id):
    """Return every copy of the session's transcript, largest first."""
    name = session_id + ".jsonl"
    copies = []
    for folder in os.listdir(projects_dir):
        path = os.path.join(projects_dir, folder, name)
        if os.path.isfile(path):
            copies.append(path)
    return sorted(copies, key=os.path.getsize, reverse=True)


def text_length(content):
    """Return the length of a tool result's text."""
    if isinstance(content, str):
        return len(content)
    if isinstance(content, list):
        return sum(len(block.get("text", "")) for block in content
                   if isinstance(block, dict))
    return 0


def input_hint(tool_input):
    """Return a short label for a tool call: its path, command or pattern.

    A path keeps its end, because the file name is at the end.
    """
    path = tool_input.get("file_path")
    if isinstance(path, str) and path:
        return path[-HINT_LENGTH:]
    for key in ("command", "pattern", "description", "url"):
        value = tool_input.get(key)
        if isinstance(value, str) and value:
            return " ".join(value.split())[:HINT_LENGTH]
    return ""


def is_owner_message(entry):
    """Return True for a message that the owner typed."""
    if entry.get("type") != "user" or entry.get("isSidechain") or entry.get("isMeta"):
        return False
    content = entry.get("message", {}).get("content")
    if isinstance(content, list):
        if any(block.get("type") == "tool_result" for block in content
               if isinstance(block, dict)):
            return False
        content = " ".join(block.get("text", "") for block in content
                           if isinstance(block, dict))
    return isinstance(content, str) and not content.lstrip().startswith("<")


class Chain:
    """The requests and tool calls of one conversation chain."""

    def __init__(self):
        self.contexts = []
        self.models = collections.Counter()
        self.tools = collections.Counter()
        self.calls = {}
        self.first_time = None
        self.last_time = None
        self._seen = set()

    def add_assistant(self, entry):
        message = entry.get("message", {})
        message_id = message.get("id")
        if message_id not in self._seen:
            self._seen.add(message_id)
            usage = message.get("usage")
            if usage:
                self.contexts.append(context_of(usage))
            if message.get("model"):
                self.models[message["model"]] += 1
        for block in message.get("content", []):
            if isinstance(block, dict) and block.get("type") == "tool_use":
                self.tools[block["name"]] += 1
                self.calls[block["id"]] = (block["name"], block.get("input", {}))

    def add_time(self, entry):
        stamp = entry.get("timestamp")
        if stamp:
            self.first_time = self.first_time or stamp
            self.last_time = stamp


def read_subagent(path):
    """Return the chain of one subagent transcript."""
    chain = Chain()
    for entry in read_entries(path):
        chain.add_time(entry)
        if entry.get("type") == "assistant":
            chain.add_assistant(entry)
    return chain


def read_meta(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def digest_session(projects_dir, session_id, target):
    copies = find_transcripts(projects_dir, session_id)
    if not copies:
        return [f"## Session {session_id}", "", "No transcript found.", ""]
    path = copies[0]

    main = Chain()
    title = None
    versions = []
    owner_messages = 0
    compactions = 0
    api_errors = 0
    results = []
    messages_to = collections.Counter()

    for entry in read_entries(path):
        kind = entry.get("type")
        if kind == "custom-title":
            title = entry.get("customTitle", title)
        if entry.get("isSidechain"):
            continue
        main.add_time(entry)
        if entry.get("version") and entry["version"] not in versions:
            versions.append(entry["version"])
        if kind == "assistant":
            main.add_assistant(entry)
            for block in entry.get("message", {}).get("content", []):
                if (isinstance(block, dict) and block.get("type") == "tool_use"
                        and block["name"] == "SendMessage"):
                    messages_to[block.get("input", {}).get("to")] += 1
        elif kind == "user":
            if is_owner_message(entry):
                owner_messages += 1
            content = entry.get("message", {}).get("content")
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        results.append((text_length(block.get("content")),
                                        block.get("tool_use_id")))
        elif kind == "system":
            if entry.get("subtype") == "compact_boundary":
                compactions += 1
            elif entry.get("subtype") == "api_error":
                api_errors += 1

    lines = [f"## Session {session_id}" + (f": {title}" if title else ""), ""]
    lines.append(f"- Transcript: `{path}`")
    if len(copies) > 1:
        lines.append(f"  ({len(copies)} copies; the digest uses the largest)")
    lines.append(f"- Versions: {', '.join(versions) or 'unknown'}")
    lines.append(f"- Time: {main.first_time} to {main.last_time}")
    lines.append(f"- Owner messages: {owner_messages}. Requests: {len(main.contexts)}. "
                 f"Compactions: {compactions}. API errors: {api_errors}.")
    if main.contexts:
        lines.append(f"- Context: first {kilo(main.contexts[0])}, "
                     f"largest {kilo(max(main.contexts))}, last {kilo(main.contexts[-1])}")
    if main.models:
        lines.append("- Models: " + ", ".join(f"{m} ({n})" for m, n in main.models.most_common()))
    lines.append("- Tool calls: " + (", ".join(f"{t} {n}" for t, n in main.tools.most_common())
                                     or "none"))

    results.sort(reverse=True)
    if results:
        lines.append("- Largest tool results (characters):")
        for length, tool_use_id in results[:LARGEST_RESULTS]:
            name, tool_input = main.calls.get(tool_use_id, ("?", {}))
            hint = input_hint(tool_input)
            lines.append(f"  - {length} {name}" + (f": `{hint}`" if hint else ""))

    folder = os.path.join(os.path.splitext(path)[0], "subagents")
    agents = []
    if os.path.isdir(folder):
        for name in os.listdir(folder):
            if name.startswith("agent-") and name.endswith(".jsonl"):
                agent_id = name[len("agent-"):-len(".jsonl")]
                chain = read_subagent(os.path.join(folder, name))
                meta = read_meta(os.path.join(folder, name[:-len(".jsonl")] + ".meta.json"))
                agents.append((chain.first_time or "", agent_id, chain, meta))
    agents.sort(key=lambda row: row[0])

    lines.append("")
    lines.append(f"### Subagents: {len(agents)} (target {kilo(target)})")
    if agents:
        lines.append("")
        lines.append("| Agent | Type | Description | Model | Shape | Requests | Tools "
                     "| First | Last | Messages in |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|")
        for _, agent_id, chain, meta in agents:
            first = kilo(chain.contexts[0]) if chain.contexts else "-"
            last = "-"
            if chain.contexts:
                last = kilo(chain.contexts[-1])
                is_implementer = meta.get("agentType", "").endswith("implementer")
                if is_implementer and chain.contexts[-1] > target:
                    last += " over"
            model = chain.models.most_common(1)[0][0] if chain.models else "-"
            lines.append(
                f"| {agent_id} | {meta.get('agentType', '-')} "
                f"| {meta.get('description', '-')} | {model} "
                f"| {meta.get('requestShape', '-')} | {len(chain.contexts)} "
                f"| {sum(chain.tools.values())} | {first} | {last} "
                f"| {messages_to.get(agent_id, 0)} |")
    lines.append("")
    return lines


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("session_ids", nargs="+", metavar="SESSION_ID")
    parser.add_argument("--projects-dir",
                        default=os.path.join(os.path.expanduser("~"), ".claude", "projects"))
    parser.add_argument("--target", type=int, default=100000,
                        help="the sizing target for one implementer, in tokens")
    args = parser.parse_args()
    if not os.path.isdir(args.projects_dir):
        sys.exit(f"error: no projects folder at {args.projects_dir}")
    out = []
    for session_id in args.session_ids:
        out.extend(digest_session(args.projects_dir, session_id, args.target))
    sys.stdout.reconfigure(encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()

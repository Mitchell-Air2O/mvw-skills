#!/usr/bin/env python3
"""Print one line about a subagent's context and the session's context.

Hook mode (no arguments): a PostToolUse hook for the Agent tool. After a
foreground subagent returns, it adds the line to the session's context. The
event is JSON on stdin.

Command-line mode: print the same line from the transcripts. Use it for a
subagent that ran in the background:
    context_report.py --session SESSION_ID --agent AGENT_ID [--projects-dir DIR]

The line gives the subagent's context at its last request, its model, its
tool-call count, and the session's own context.

Context is the input tokens of one request: input_tokens plus
cache_read_input_tokens plus cache_creation_input_tokens. session_digest.py
uses the same definition.

A background call returns no usage. The hook then adds nothing.
The transcript can lag the current turn, so the session's own context can be
one request old.
"""

import argparse
import json
import os
import sys

import session_digest


def context_of(usage):
    """Return the input tokens of one request from its usage block."""
    return (usage.get("input_tokens", 0)
            + usage.get("cache_read_input_tokens", 0)
            + usage.get("cache_creation_input_tokens", 0))


def session_context(transcript_path):
    """Return the context of the newest main-chain request, or None."""
    last = None
    try:
        with open(transcript_path, encoding="utf-8") as f:
            for line in f:
                if '"assistant"' not in line:
                    continue
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                if entry.get("type") != "assistant" or entry.get("isSidechain"):
                    continue
                usage = entry.get("message", {}).get("usage")
                if usage:
                    last = context_of(usage)
    except OSError:
        return None
    return last


def kilo(tokens):
    return f"{round(tokens / 1000)}k"


def report_line(agent_type, agent_id, context, model, tool_calls, own):
    """Return the report line. Omit a part whose value is missing."""
    parts = [f"{agent_type} {agent_id} ended at {kilo(context)} context"]
    if model:
        parts.append(f"model {model}")
    if tool_calls is not None:
        parts.append(f"{tool_calls} tool calls")
    line = ", ".join(parts) + "."
    if own is not None:
        line += f" Your own context: {kilo(own)}."
    return line


def run_hook():
    event = json.load(sys.stdin)
    response = event.get("tool_response")
    if not isinstance(response, dict) or not response.get("usage"):
        return
    agent_type = (response.get("agentType")
                  or event.get("tool_input", {}).get("subagent_type")
                  or "agent")
    line = report_line(agent_type, response.get("agentId", "?"),
                       context_of(response["usage"]),
                       response.get("resolvedModel"),
                       response.get("totalToolUseCount"),
                       session_context(event.get("transcript_path", "")))
    json.dump({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                      "additionalContext": line}}, sys.stdout)


def run_command_line(args):
    if not os.path.isdir(args.projects_dir):
        sys.exit(f"error: no projects folder at {args.projects_dir}")
    copies = session_digest.find_transcripts(args.projects_dir, args.session)
    if not copies:
        sys.exit(f"error: no transcript for session {args.session} "
                 f"in {args.projects_dir}")
    name = f"agent-{args.agent}"
    for copy in copies:
        folder = os.path.join(os.path.splitext(copy)[0], "subagents")
        path = os.path.join(folder, name + ".jsonl")
        if os.path.isfile(path):
            break
    else:
        sys.exit(f"error: no transcript for agent {args.agent} "
                 f"in session {args.session}")
    chain = session_digest.read_subagent(path)
    if not chain.contexts:
        sys.exit(f"error: no request with usage in {path}")
    meta = session_digest.read_meta(os.path.join(folder, name + ".meta.json"))
    model = chain.models.most_common(1)[0][0] if chain.models else None
    print(report_line(meta.get("agentType") or "agent", args.agent,
                      chain.contexts[-1], model, sum(chain.tools.values()),
                      session_context(copies[0])))


def main():
    if len(sys.argv) == 1:
        run_hook()
        return
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--session", required=True)
    parser.add_argument("--agent", required=True)
    parser.add_argument("--projects-dir",
                        default=os.path.join(os.path.expanduser("~"), ".claude", "projects"))
    run_command_line(parser.parse_args())


if __name__ == "__main__":
    main()

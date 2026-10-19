#!/usr/bin/env python3
"""PostToolUse hook for the Agent tool.

After a foreground subagent returns, add one line to the session's context:
the subagent's context at its last request, and the session's own context.

Context is the input tokens of one request: input_tokens plus
cache_read_input_tokens plus cache_creation_input_tokens. session_digest.py
uses the same definition.

A background call returns no usage. The hook then adds nothing.
The transcript can lag the current turn, so the session's own context can be
one request old.
"""

import json
import sys


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


def main():
    event = json.load(sys.stdin)
    response = event.get("tool_response")
    if not isinstance(response, dict) or not response.get("usage"):
        return
    agent_type = (response.get("agentType")
                  or event.get("tool_input", {}).get("subagent_type")
                  or "agent")
    parts = [f"{agent_type} {response.get('agentId', '?')} ended at "
             f"{kilo(context_of(response['usage']))} context"]
    if response.get("resolvedModel"):
        parts.append(f"model {response['resolvedModel']}")
    if response.get("totalToolUseCount") is not None:
        parts.append(f"{response['totalToolUseCount']} tool calls")
    line = ", ".join(parts) + "."
    own = session_context(event.get("transcript_path", ""))
    if own is not None:
        line += f" Your own context: {kilo(own)}."
    json.dump({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                      "additionalContext": line}}, sys.stdout)


if __name__ == "__main__":
    main()

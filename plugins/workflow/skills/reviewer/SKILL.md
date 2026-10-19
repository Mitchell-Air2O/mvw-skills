---
name: reviewer
description: Review all the work of a plan, run a retro on the sessions of that plan, then ask the owner if the work is ready to close out. Use when the owner runs /reviewer, or when a builder session finishes its last stage.
---

# Reviewer

You review the work of a plan, then you run a retro on its sessions. You propose only.
The owner picks. The argument is the plan path, a branch or a pull request. With no
argument, use the plan or the branch of the current session.

The review and the retro are read-only. Section 3 applies the picks and asks the
close-out question, in the session that talks to the owner.

## 1. Review

1. Read the plan, if there is one. Its Decisions section states what the work must do.
2. Read the project instructions. Find the project's review checklist. Follow it. If the
   project has none, review for correctness, for the project instructions and for the
   plan's decisions.
3. Get the full diff of the work: the branch against its merge base with the base
   branch.
4. Read each changed file around each change. Verify each finding with a tool before you
   report it. Label a finding that you cannot verify as an assumption.

Report, in this order:

- **Recap**: what the work does, in a few lines.
- **Defects**: wrong behavior, ranked by what to act on first, with `file:line`.
- **Improvements**: contract risks, then cosmetic items, with `file:line`.
- **Follow-ups**: work outside the plan, one line each.
- What you verified and what you did not.

## 2. Retro

You propose changes to the agent's environment, so that later sessions do better.

1. Read the session digest of the plan's sessions. The `Sessions:` line of the plan gives
   the session IDs. Do not read the raw transcripts.
2. Look for candidates in these categories:
   - **Navigation**: a session took long to find a file or a fact. A pointer in the
     project instructions or a rule file can help.
   - **Automated checks**: a session made a mistake that a check can catch. Read the
     project's build checks and CI first. A check that exists but does not run is the
     finding. A mechanical rule (a pattern, a banned call, a file location) gets a check,
     not a line of prose.
   - **Review rules**: the review missed a mistake. Add, clarify or remove a rule in the
     project's review checklist. Keep prose rules for judgment calls.
   - **Stage size**: an implementer overran the sizing target, or a stage needed a fresh
     implementer. Say what made the stage too large.
   - **Model and effort**: a stage failed at its row of the table, or ran at a higher row
     than it needed.
   - **Tool economy**: a tool call cost many tokens and a cheaper call does the same job.
   - **Instructions that do nothing**: a line in the instructions that changes no
     behavior.
   - **Information access**: a session lacked a fact that it needed.
3. Rank the proposals by severity. Number them. Each proposal names its target file and
   the change. The targets are:
   - the project: the project instructions, rule files, checks, the memory folder;
   - the framework: the skills and agents in `Mitchell-Air2O/mvw-skills`;
   - the owner's global instructions (`~/.claude/CLAUDE.md` in Claude Code).
4. Write each proposal by the project's writing rules.

## 3. Picks and close-out

The owner picks proposals by number. Apply each pick:

- A project pick goes on a second branch, by the project's branch rule. One change per
  branch.
- A framework pick: commit and push it to `mvw-skills`.
- A pick for the owner's global instructions: edit the file in place.

Then ask the owner one question: is the work ready to close out? On yes, the builder
does the close-out steps of the `builder` skill.

## In Claude Code

- Run sections 1 and 2 in the read-only agent: the `Agent` tool with
  `subagent_type: "workflow:reviewer"`, `model: "opus"`, `effort: "high"` and
  `run_in_background: false`. Give it the plan path, the branch, the base branch and the
  path of this file: `${CLAUDE_SKILL_DIR}/SKILL.md`.
- The digest: `python "${CLAUDE_PLUGIN_ROOT}/scripts/session_digest.py"` with the
  session IDs of the `Sessions:` line.
- Run section 3 in the session that talks to the owner.

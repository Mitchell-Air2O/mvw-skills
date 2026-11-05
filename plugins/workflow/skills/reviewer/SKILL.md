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

## Finding categories

Every report sorts its findings into these categories. This table is the only full
definition.

| ID | Category | Meaning |
|---|---|---|
| D# | Defect | The work behaves wrongly now, or it breaks a stated rule or decision. |
| R# | Contract risk | The work is correct now, but it depends on a condition that nothing checks or enforces. |
| C# | Cosmetic | Wording, style or duplicated text. No behavior changes. |
| F# | Follow-up | A problem outside the scope of the plan. |
| P# | Proposal | A retro change to the instructions, the checks or the framework. |

IDs are unique within a plan. Numbering continues across the reviews of one plan: a plan
review gives D1 to D3, and the work review after it starts at D4. A review that has no
plan starts each category at 1.

Open questions to the owner keep plain numbers: "1. **D4**, the raw value stays set after a
timeout (`Sensor.cpp:785`): fix on this branch?". A plan, a report and a question name a
decision as "Decision N" in full, never "D" with a number, because D# names a defect.

A message to the owner restates each finding, proposal and decision that it names: the ID,
one sentence on what it says, and `file:line` where it has one. This applies to each
message, also to a later message about the same item. Never send an ID alone. The plan
holds each item in full: the findings and the proposals under `## Review results`, the
decisions under `## Decisions`. A message that names more than three items also gives the
plan path and the section.

## 1. Review

1. Read the plan, if there is one. Its Decisions section states what the work must do.
2. Read the project instructions. Find the project's review checklist, its retro queue
   and its open-work file. Follow the checklist. If the project has no checklist, review
   for correctness, for the project instructions and for the plan's decisions.
3. Find the work: the range `<base>...<branch>`, the branch against its merge base with
   the base branch. If the plan spans more than one repository, or has commits directly
   on a base branch, take each commit range `<first>^..<last>` from the stage status
   lines of the plan. Review each range. Run `git diff --stat <range>` first. Read the
   diff one file at a time with `git diff <range> -- <file>`. Read the diff of each file
   one time. For a rename across many files, check with a grep for the old term and the
   new term, not with the full diff.
4. Read each changed file around each change. Verify each finding with a tool before you
   report it. Label a finding that you cannot verify as an assumption. When the work
   changes a procedure in a skill or an agent file, walk each entry into the procedure: a
   fresh session, a session that resumes after a hand-off, and a session after a review.
   Check that each entry reaches the right step and reads each section that the step
   needs.

The report holds findings only. It has no tasks, no stages and no fix order. List the
findings by category, in this order: defects (D#), contract risks (R#), cosmetic items
(C#), follow-ups (F#). Within a category, rank the findings by what to act on first. The
P# come from the retro (section 2). Leave out an empty category.

Write each finding as one entry: the ID, one sentence on what is wrong, `file:line`, and
the effect. An entry can name an obvious fix in one clause ("use `uint32_t`").

End the report with **Assumptions and own decisions**. Mark each assumption: a claim that
you did not check with a tool. Mark each decision that you made and that neither the plan
nor the owner made. Do not list what you checked.

## 2. Retro

You propose changes to the agent's environment, so that later sessions do better.

1. Read the session digest of the plan's sessions. The `Sessions:` line of the plan gives
   the session IDs. Do not read the raw transcripts. Compare the owner messages with the
   work. Name each request that the work does not meet.
2. Look for candidates in these categories:
   - **Navigation**: a session took long to find a file or a fact. A pointer in the
     project instructions or a rule file can help.
   - **Automated checks**: a session made a mistake that a check can catch. Read the
     project's build checks and CI first. A check that exists but does not run is the
     finding. A mechanical rule (a pattern, a banned call, a file location) gets a check,
     not a line of prose.
   - **Review rules**: the review missed a mistake. Add, clarify or remove a rule in the
     project's review checklist. Keep prose rules for judgment calls.
   - **Stage size**: the builder's grouping of the tasks into stages. A worker overran
     the sizing target, a stage needed a fresh worker, or two stages loaded the same
     context. Say what made the stage too large, or which stages to merge.
   - **Model and effort**: a stage failed at its row of the table, or ran at a higher row
     than it needed.
   - **Tool economy**: a tool call cost many tokens and a cheaper call does the same job.
   - **Instructions that do nothing**: a line in the instructions that changes no
     behavior.
   - **Information access**: a session lacked a fact that it needed.
3. Rank the proposals by severity. Number them P1, P2 and so on, by the ID rule of
   "Finding categories". Each proposal names its target file and the change. The targets
   are:
   - the project: the project instructions, rule files, checks, the memory folder;
   - the framework: the skills and agents in `Mitchell-Air2O/mvw-skills`;
   - the owner's global instructions (`~/.claude/CLAUDE.md` in Claude Code).
4. Write each proposal by the project's writing rules.

## 3. Picks and close-out

The builder writes the report into the plan under `## Review results`, with the text of
each P# in full (section 7 of the `builder` skill). It shows the owner the report from
there. Apply only the text that the owner saw.

The owner picks by ID:

- D#, R# and C#: fix, defer or drop. A fix becomes a fix task of the plan. A deferred
  finding becomes an F#: it takes the next free F number of the plan, and the entry names
  its old ID ("F3 (was D4)").
- P#: pick or defer.
- F#: no pick. Each F# goes to the project's open-work file. If the project has no
  open-work file, report the F# to the owner.

Apply each P# pick:

- A project pick goes on a second branch, by the project's branch rule. One change per
  branch.
- A framework pick: commit and push it to `mvw-skills`. Then update the installed plugin
  by the planner's update step, so that the next session of the plan loads the pick.
  Read the `version` of `workflow@mvw-skills` in `~/.claude/plugins/installed_plugins.json`
  and write it into the plan. If it is not the version that you pushed, tell the owner.
- A pick for the owner's global instructions: edit the file in place.

A P# that the owner defers goes into the project's retro queue, under the plan's heading,
with its target file and the change. If the project has no retro queue, report the
deferred P# to the owner.

When the owner picks a fix, the builder hands off first. The new builder makes the fix
stages, then applies the P# picks (section 7 of the `builder` skill).

Then ask the owner one question: is the work ready to close out? On yes, the builder
does the close-out steps of the `builder` skill.

## In Claude Code

- Run sections 1 and 2 in the read-only agent: the `Agent` tool with
  `subagent_type: "workflow:reviewer"`, `model: "opus"`, `effort: "high"` and
  `run_in_background: false` where the tool takes it. Give it the plan path, the branch,
  the base branch and the path of this file: `${CLAUDE_SKILL_DIR}/SKILL.md`.
- A session that another session started runs its subagents in the background, and the
  owner accepts that. Wait for the task notification, and read the report after it. A
  background call gets no hook line. Then run
  `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/context_report.py" --session ${CLAUDE_SESSION_ID} --agent <agent ID>`
  for the reviewer's context. The `Agent` tool result gives the agent ID.
- If the `workflow:reviewer` agent type is not found, the session started before the
  plugin was installed. Use `subagent_type: "general-purpose"` with the same `model`
  and `effort`. Put the text of
  `${CLAUDE_PLUGIN_ROOT}/agents/reviewer.md` in the prompt. That agent can edit files,
  so the prompt states the read-only limit. Tell the owner to run
  `claude plugin install workflow@mvw-skills --scope project` and to start the next
  session after that.
- The digest: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/session_digest.py"` with the
  session IDs of the `Sessions:` line.
- Run section 3 in the session that talks to the owner.

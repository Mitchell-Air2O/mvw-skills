---
name: builder
description: Run an approved plan. Group its tasks into stages, start one worker subagent per stage, review each diff, commit, and keep the plan current. Use when the owner runs /builder with a plan path, or starts the builder card from a planner session.
---

# Builder

You run an approved plan in a fresh session. The argument is the plan path. You group the
plan's tasks into stages and pick the model and the effort of each stage. You start one
worker per stage, review each diff, commit, and keep the plan current. You keep the
design and the review. The worker makes the edit and the build.

## 1. Start

1. Read the full plan. Its Decisions section, its tasks and its stage results are the
   only source of truth. The conversation that made the plan is not.
2. Read the project instructions. Find the build command, the review checklist, the
   branch rule, the commit rule, the merge procedure and the declined-designs file.
3. Find the plan in the main checkout (the first entry of `git worktree list`). Read and
   update it by its full path there, also from a worktree. Never copy it into a worktree.
4. Add your session ID and your role to the plan's `Sessions:` line.
5. Set your session title to the branch name in the plan's Status line. In a tool that
   cannot rename a session, skip this step.
6. Work on that branch. If neither the branch nor a worktree exists, create them by the
   project's branch rule. If your session already has a worktree on another branch (a
   tool can name the worktree and its branch), create the plan's branch in that worktree
   by the project's branch rule. Then delete the other branch if it holds no commits of
   its own. The worktree folder name can differ from the branch name.
7. Check the tool version. See "In Claude Code".
8. If the planner's session started yours, move your session to top level. The owner
   then talks to you alone, and the planner gets no report of your turns. See
   "In Claude Code".

## 2. Group the tasks into stages

Before the first worker starts, group the plan's tasks into stages. A stage is one worker
run or one builder edit. If the plan has a `## Stages` section, use it.

- Group the tasks that read the same files and rule files. Keep the dependency order.
- Size each stage so that its worker ends at about 100k tokens of context. Count what the
  worker reads, not what it changes. The target is for sizing. It is not a cutoff.
- A large source file and edits of another kind (web, docs, rule files) are two stages.
- Count each rule file and doc that a stage reads or updates in its size. When a stage
  that changes behavior also updates more than about three rule files or docs, or
  changes code in more than two languages, put the doc updates in a following stage at
  row 1 of the table. That stage reads the landed diff.
- Make a task yourself only when the edit is a few lines in one file. Send a prose edit
  across several files to a worker at row 1 of the table. The brief names the plan's
  decisions. It does not copy their text.
- Pick the model and the effort of each worker stage from the table (section 4).

Write a `## Stages` section into the plan: for each stage, its tasks and who makes it
(the builder, or the model and the effort). A builder after a hand-off resumes from this
section. You can regroup the stages that have not started. Update the section first.

## 3. The stage loop

Do the first stage that is not done. Then do the next. After the owner's "go", do not
stop between stages. Stop only for:

- a decision that the plan does not make;
- a hardware step;
- a hand-off (section 6).

For each stage:

1. If the stage names the builder, make the stage yourself. Go to step 5.
2. Write the brief. The brief holds only the context that the stage needs, not the
   conversation:
   - the goal;
   - the files to change;
   - the rule files and documents to read;
   - the pattern to follow;
   - the helpers to reuse or to add;
   - what done looks like;
   - the build to run.
3. Start the worker with the model and the effort of its stage set on the call. The call
   can start in the background. Then wait for its notification, and read the report
   after it.
4. Read the worker's report. The owner talks only to you, never to a worker.
   - A question: answer it from the plan if the plan settles it. If not, ask the owner
     yourself (the first stop rule). Then resume the worker with the answer by
     section 5, or start a fresh one if the answer changes the design.
   - A finding outside the brief: write it in the plan under the stage, one line each.
     The owner and the reviewer read it there.
5. Review the diff by the project's review checklist. Run `git status --short` and
   `git diff --stat HEAD` first. Read the diff one file at a time with
   `git diff HEAD -- <file>`. Read the diff of each file one time. Read each new file
   that `git status` lists in full. For a rename across many files, check with a grep for
   the old term and the new term, not with the full diff.
6. Fix a small defect yourself, or resume the worker by section 5. Build again.
7. Commit by the project's commit rule. Make one commit per stage. The body lists the
   tasks of the stage.
8. Mark the stage done in the plan with the date, the commit and the worker's token
   count. Write the new `**Next step:**`.

A stage overruns when its worker ends far above the sizing target. Finish the stage
with a fresh worker. Write the overrun in the plan, so that the retro reports the
stage as too large.

When you ask the owner a question, use the grill format of the `planner` skill: numbered,
with a `(rec)` answer. For each option, say what it changes in the plan: the decisions, the
tasks and the stages. Write each answer into `## Decisions` with the date. Update the
tasks and the stages that the answer changes before the next worker starts.

## 4. Model and effort

Set both on each worker call. Never leave the effort to the default.

| The stage | Model | Effort |
|---|---|---|
| The brief names every edit, or the stage is mostly text edits with at most a one-line logic change. No decision is left. | Sonnet | medium |
| Several files, a new helper, or build errors to work through (the default) | Sonnet | high |
| Judgment that the brief cannot settle (concurrency, numerics, a subtle invariant), or a Sonnet run failed on the stage | Opus | high |
| Opus at high effort failed on the same stage | Opus | xhigh |

Pick the row of each stage when you group the tasks (section 2). A failed run moves the
stage one row down.

## 5. Resume or fresh

- Resume a worker only for a small fix to its own stage or the answer to its
  question, and only when it ended under the sizing target.
- Never send a design change into a running worker. Stop it. Start a fresh one with
  a revised brief.
- The worker has a turn limit. It is a checkpoint, not a context cutoff. At the
  limit, control returns to you. Resume the worker by the first rule, or start a
  fresh one with a brief that names the work left.

## 6. Your own context

You have no token limit. Hand off when your own context passes about 250k tokens, or
earlier when you judge it too large. In Claude Code, the hook line after each worker gives
the figure. Then, at a stage boundary:

1. Update the plan's `**Next step:**`, so that a new session can resume from the plan
   file alone.
2. Offer a fresh builder session that runs `/builder <full plan path>`.
3. Stop.

## 7. Review and close-out

After the last stage:

1. Run the reviewer on all the work of the plan (see the `reviewer` skill). Give the
   owner its report.
2. Apply the retro picks that the owner makes, by the `reviewer` skill.
3. Ask the close-out question of the `reviewer` skill.

On yes, do these steps in order. Stop at the first step that fails, and report it.

1. Copy each rejected alternative of the plan that a later change can propose again into
   the project's declined-designs file, if the project has one. Commit it on the last
   branch.
2. Archive the plan by the project's plan rules. Do every step that those rules give, for
   example a list of open hardware checks or an index of plans. On the last branch, add
   the plan as `<plan folder>/archive/<NAME>_PLAN.md`. Commit it. Compare the archived
   copy with the top-level copy byte for byte. If they are equal, delete the top-level
   copy. The paths differ, so the merge has no conflict.
3. Publish by the project's merge procedure.
4. Delete the branch, local and on origin. Remove the worktree, except where step 5
   removes it (see "In Claude Code").
5. Archive the sessions in the plan's `Sessions:` line together: the planner's session
   first, your own session last.

## In Claude Code

- Version: the `effort` parameter of the `Agent` tool needs Claude Code v2.1.292 or
  later. Read the `version` field of the newest entry in your session transcript
  (`~/.claude/projects/<project>/${CLAUDE_SESSION_ID}.jsonl`). If the version is older,
  or you cannot read it, stop. Report the version and the minimum. Do not run a stage at
  the wrong effort.
- If the environment variable `CLAUDE_CODE_EFFORT_LEVEL` is set, it overrides the
  `effort` parameter. Stop and report it.
- Your session ID is `${CLAUDE_SESSION_ID}`.
- Set the session title: in the Claude desktop app, `set_session_title` with
  `session_id: "self"`; in the CLI, `/rename`.
- The plan file: in the Claude desktop app, a hook refuses `Edit` on a file
  in the main checkout from a worktree session. Update the plan with a short Python
  script through `Bash`. The script replaces each exact text one time and stops if the
  text is not found exactly one time.
- A running session and its subagents keep the instruction text that they loaded at
  their start. After you edit the owner's global instructions, tell the owner that the
  change applies from the next session.
- Start the worker with the `Agent` tool: `subagent_type: "workflow:worker"`,
  `model` (`sonnet` or `opus`), `effort` (`medium`, `high` or `xhigh`), and
  `run_in_background: false` where the tool takes it. A session that another session
  started runs its subagents in the background, and the owner accepts that. A
  background call returns at once. Wait for the task notification.
- If the `workflow:worker` agent type is not found, the session started before the
  plugin was installed. Use `subagent_type: "general-purpose"` with the same `model`
  and `effort`. Put the text of `${CLAUDE_PLUGIN_ROOT}/agents/worker.md` in the prompt
  before the brief. Tell the owner to run
  `claude plugin install workflow@mvw-skills --scope project` and to start the next
  session after that.
- The plugin's hook adds a line after each foreground worker returns: the worker's
  tokens and your own context. Use the first for section 5 and the retro. Use the second
  for section 6. A background worker gets no hook line. When its report arrives, run
  `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/context_report.py" --session ${CLAUDE_SESSION_ID} --agent <agent ID>`.
  It prints the same line. The `Agent` tool result gives the agent ID.
- Resume a worker with `SendMessage` to its agent ID. Stop one with `TaskStop`.
- Top level (section 1, step 8): in the Claude desktop app, the planner's card starts the
  builder as a side session of the planner. Call `detach_session` with
  `session_id: "self"`. The sidebar then shows the builder at top level, and the app no
  longer sends its reports to the planner. The planner is no longer archived with it, so
  close-out step 5 archives both. The CLI has no side sessions; skip the step.
- The builder hand-off: in the Claude desktop app, propose a new session as a card. Use
  `start_session` with `initiation: "own_initiative"`, `context: "fresh"`,
  `title: <branch name>`, `prompt: "/builder <full plan path>"`, `background` (the goal
  of the plan, its full path and the stage to resume, at least 80 characters),
  `use_worktree: true` and `branch_name: <branch name>`. The app adds a prefix and a
  suffix to the branch name. The new builder creates the plan's branch by section 1. In
  the CLI, tell the owner to start a new session and run `/builder <full plan path>`.
- Archive a session with `archive_session` in the Claude desktop app. It also removes the
  session's worktree, so close-out step 4 does not remove it. The CLI has no such step;
  skip it, and remove the worktree in step 4.

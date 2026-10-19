---
name: builder
description: Run an approved plan stage by stage. Start one implementer subagent per stage, review each diff, commit, and keep the plan current. Use when the owner runs /builder with a plan path, or starts the builder card from a planner session.
---

# Builder

You run an approved plan in a fresh session. The argument is the plan path. You start one
implementer per stage, review each diff, commit, and keep the plan current. You keep the
design and the review. The implementer makes the edit and the build.

## 1. Start

1. Read the full plan. Its Decisions section and its stage results are the only source of
   truth. The conversation that made the plan is not.
2. Read the project instructions. Find the build command, the review checklist, the
   branch rule, the commit rule and the merge procedure.
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

## 2. The stage loop

Do the first stage that is not done. Then do the next. After the owner's "go", do not
stop between stages. Stop only for:

- a decision that the plan does not make;
- a hardware step;
- a hand-off (section 5).

For each stage:

1. If the stage's "Who" line names the builder, make the stage yourself. Go to step 5.
2. Write the brief. The brief holds only the context that the stage needs, not the
   conversation:
   - the goal;
   - the files to change;
   - the rule files and documents to read;
   - the pattern to follow;
   - the helpers to reuse or to add;
   - what done looks like;
   - the build to run.
3. Pick the model and the effort from the table (section 3). Start the implementer in the
   foreground, with both values set on the call.
4. Read the implementer's report.
5. Read the full diff. Review it by the project's review checklist.
6. Fix a small defect yourself, or resume the implementer by section 4. Build again.
7. Commit by the project's commit rule.
8. Mark the stage done in the plan with the date. Write the new `**Next step:**`.

A stage overruns when its implementer ends far above the sizing target. Finish the stage
with a fresh implementer. Never split the stage. Write the overrun in the plan, so that
the retro reports the stage as too large.

## 3. Model and effort

Set both on each implementer call. Never leave the effort to the default.

| The stage | Model | Effort |
|---|---|---|
| The brief names every edit. No decision is left. | Sonnet | medium |
| Several files, a new helper, or build errors to work through (the default) | Sonnet | high |
| Judgment that the brief cannot settle (concurrency, numerics, a subtle invariant), or a Sonnet run failed on the stage | Opus | high |
| Opus at high effort failed on the same stage | Opus | xhigh |

The plan's "Who" line gives the row. A failed run moves the stage one row down.

## 4. Resume or fresh

- Resume an implementer only for a small fix to its own stage, and only when it ended
  under the sizing target.
- Never send a design change into a running implementer. Stop it. Start a fresh one with
  a revised brief.
- The implementer has a turn limit. It is a checkpoint, not a context cutoff. At the
  limit, control returns to you. Resume the implementer by the first rule, or start a
  fresh one with a brief that names the work left.

## 5. Your own context

You have no token limit. You decide when your context is too large. Then, at a stage
boundary:

1. Update the plan's `**Next step:**`, so that a new session can resume from the plan
   file alone.
2. Offer a fresh builder session that runs `/builder <full plan path>`.
3. Stop.

## 6. Review and close-out

After the last stage:

1. Run the reviewer on all the work of the plan (see the `reviewer` skill). Give the
   owner its report.
2. Apply the retro picks that the owner makes, by the `reviewer` skill.
3. Ask the close-out question of the `reviewer` skill.

On yes, do these steps in order. Stop at the first step that fails, and report it.

1. Archive the plan by the project's plan rules. Do every step that those rules give, for
   example a list of open hardware checks or an index of plans. On the last branch, add
   the plan as `<plan folder>/archive/<NAME>_PLAN.md`. Commit it. Compare the archived
   copy with the top-level copy byte for byte. If they are equal, delete the top-level
   copy. The paths differ, so the merge has no conflict.
2. Publish by the project's merge procedure.
3. Delete the branch, local and on origin. Remove the worktree, except where step 4
   removes it (see "In Claude Code").
4. Archive the sessions in the plan's `Sessions:` line. Archive your own session last.

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
- The plan file: in the Claude desktop app, a hook refuses `Edit` and `Write` on a file
  in the main checkout from a worktree session. Update the plan with a short Python
  script through `Bash`. The script replaces each exact text one time and stops if the
  text is not found exactly one time.
- Start the implementer with the `Agent` tool: `subagent_type: "workflow:implementer"`,
  `model` (`sonnet` or `opus`), `effort` (`medium`, `high` or `xhigh`), and
  `run_in_background: false`. A foreground call returns the token count of the
  implementer.
- If the `workflow:implementer` agent type is not found, the session started before the
  plugin was installed. Use `subagent_type: "general-purpose"` with the same `model`,
  `effort` and `run_in_background`. Put the text of
  `${CLAUDE_PLUGIN_ROOT}/agents/implementer.md` in the prompt before the brief. Tell the
  owner to run `claude plugin install workflow@mvw-skills --scope project` and to start
  the next session after that.
- The plugin's hook adds a line after each implementer returns: the implementer's tokens
  and your own context. Use the first for section 4 and the retro. Use the second for
  section 5.
- Resume an implementer with `SendMessage` to its agent ID. Stop one with `TaskStop`.
- The builder hand-off: in the Claude desktop app, propose a new session as a card. Use
  `start_session` with `initiation: "own_initiative"`, `context: "fresh"`,
  `title: <branch name>`, `prompt: "/builder <full plan path>"`, `background` (the goal
  of the plan, its full path and the stage to resume, at least 80 characters),
  `use_worktree: true` and `branch_name: <branch name>`. The app adds a prefix and a
  suffix to the branch name. The new builder creates the plan's branch by section 1. In
  the CLI, tell the owner to start a new session and run `/builder <full plan path>`.
- Archive a session with `archive_session` in the Claude desktop app. It also removes the
  session's worktree, so close-out step 3 does not remove it. The CLI has no such step;
  skip it, and remove the worktree in step 3.

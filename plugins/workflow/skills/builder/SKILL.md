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
6. Work on that branch, in a worktree of the same name. If neither exists, create them by
   the project's branch rule.
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

1. Archive the plan. On the last branch, add the plan as
   `<plan folder>/archive/<NAME>_PLAN.md`. Commit it. Compare the archived copy with the
   top-level copy byte for byte. If they are equal, delete the top-level copy. The paths
   differ, so the merge has no conflict.
2. Publish by the project's merge procedure.
3. Remove the worktree. Delete the branch, local and on origin.
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
- Set the session title: in the Claude desktop app, `set_session_title`; in the CLI,
  `/rename`.
- Start the implementer with the `Agent` tool: `subagent_type: "workflow:implementer"`,
  `model` (`sonnet` or `opus`), `effort` (`medium`, `high` or `xhigh`), and
  `run_in_background: false`. A foreground call returns the token count of the
  implementer.
- The plugin's hook adds a line after each implementer returns: the implementer's tokens
  and your own context. Use the first for section 4 and the retro. Use the second for
  section 5.
- Resume an implementer with `SendMessage` to its agent ID. Stop one with `TaskStop`.
- The builder hand-off: in the Claude desktop app, propose a new session as a card
  (`start_session`, `context: "fresh"`) with the prompt `/builder <full plan path>`. In
  the CLI, tell the owner to start a new session and run that command.
- Archive a session with `archive_session` in the Claude desktop app. The CLI has no
  such step; skip it.

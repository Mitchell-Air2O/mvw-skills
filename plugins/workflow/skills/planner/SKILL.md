---
name: planner
description: Interview the owner about a change (the grill), then write a plan of tasks that a builder session runs. Use when the owner runs /planner or asks to plan a change of more than about three steps.
---

# Planner

You interview the owner until you both understand the change. Then you write the plan.
Your session ends when the owner approves the plan. A builder session in fresh context
runs it.

## 1. Read the project values

First, update the `workflow` plugin to its newest version, so that the plan and its
builder use the newest skills (see "In Claude Code"). If the update fails, tell the
owner, and go on with the version that runs.

Read the project instructions (`AGENTS.md`, `CLAUDE.md` or the equivalent). Find these
values:

- the build command;
- the review checklist (a skill or a document);
- the plan folder (default `plans/`);
- the memory folder, if the project has one;
- the declined-designs file, if the project has one;
- the branch naming rule;
- the merge procedure.

If the project names no value that the plan needs, ask the owner in the first round.

## 2. The grill

Map the change as a design tree. Each decision has branches: the decisions that depend
on it.

Work the tree in rounds. The frontier is each open decision whose prerequisites are
settled. Ask the full frontier in one round. Then wait for the answers.

- Number each question. The owner answers by number.
- Give each question your recommended answer, marked `(rec)`. Word the question so that
  "yes" accepts the recommended answer.
- "rec" from the owner accepts the recommended answer. "rec" alone accepts every
  recommended answer of the round.
- A question that depends on another open question of the round goes in a later round.
- After each round, compute the frontier again and ask the next round.

Format of a round:

```
1. **<title>**: <the question, with the options>
   (rec) <your recommended answer>

2. **<title>**: ...
```

Facts are your job. Decisions are the owner's job. Never ask the owner for a fact that
you can look up.

- Look up a short fact yourself.
- Read yourself the code that you must reason about to recommend an answer.
- Read the project's declined-designs file before you recommend an answer.
- For a broad search where only the conclusion matters, start a read-only subagent on a
  cheaper model, in the background. Meanwhile, ask the questions that do not depend on
  the search. A question that depends on the search waits for the result.
- Split a broad audit so that each subagent reads about 100k tokens: give each one a part
  of the code. Ask for findings with file:line only, not quotes of the code.

The grill is done when the frontier is empty: you visited each branch, and you assume
nothing in silence. Do not write the plan until the owner confirms that you share one
understanding.

## 3. List the tasks

You list the tasks. The builder groups them into stages and picks the model and the
effort of each stage. Pick no stage, no model and no effort.

Each task names:

- the goal;
- the files to change;
- the rule files and documents to read;
- the tasks that it depends on;
- the behavior change (yes or none);
- the verify step.

Each verify step names a command and an output that exists after the task lands. When a
decision changes a rule that the docs state, the verify step greps for the old wording
in every file that states the rule: the framework, the project instructions, the rule
files and the memory. A grep for the renamed files alone is not enough.

## 4. Pick the name

Pick the branch name by the project's naming rule. The sessions of the plan use the same
name as their title. The worktree folder name can differ, because a tool can name the
worktree.

- Write the branch name in the plan's Status line.
- Set your session title to the branch name. In a tool that cannot rename a session,
  skip this step.

## 5. Write the plan

Save the plan in the main checkout, never in a worktree. The main checkout is the first
entry of `git worktree list`. The path is `<main checkout>/<plan folder>/<NAME>_PLAN.md`.

- An active plan stays out of git. Do not commit it.
- The plan enters git one time, when the builder archives it.

The plan has these parts, in this order:

1. The title.
2. `**Status:**` with the branch name, and `**Next step:**`.
3. `## Why`: the problem and its cost.
4. `## Decisions`: each answer of the grill, numbered. The builder treats this section as
   the only source of truth. A decision that rests on a fact about the code or a tool
   (an API is safe in an interrupt, a function is inline, a call is thread-safe) has a
   `Checked:` line with the command and its result, or an `Assumption:` line. When a
   decision changes the value that a function returns, grep the callers of that function
   and name each caller in the `Checked:` line. A caller that feeds a second actuator,
   guard or module is a consumer that the decision must cover.
5. `## Rejected alternatives`: each alternative and the reason.
6. `## Sessions`: a line `Sessions:` with your session ID and your role.
7. `## Tasks`: each task, numbered, with the items of section 3. The builder adds a
   `## Stages` section before its first worker.

List the open decisions first, in one block, and stop. The owner answers them. Then
write the plan one time.

## 6. Hand off

Ask the owner to approve the plan. On approval, hand off to a builder session with fresh
context. The owner's start of that session is the "go". Your session then ends.

## In Claude Code

- The update (section 1): run `claude plugin marketplace update mvw-skills`, then
  `claude plugin update workflow@mvw-skills --scope <scope>`, with the scope that the
  project installs it in. An update applies to the sessions that start after it, so the
  builder session gets it. Your own session keeps the skill text that it loaded. If the
  version changed, read the planner skill of the new version: the folder beside
  `${CLAUDE_PLUGIN_ROOT}` that has the new version's name. Follow that text from its
  section 1.
- Your session ID is `${CLAUDE_SESSION_ID}`. Write it in the `Sessions:` line.
- Set the session title: in the Claude desktop app, `set_session_title` with
  `session_id: "self"`; in the CLI, `/rename`.
- For a broad search, use the `Agent` tool with `subagent_type: "Explore"`,
  `model: "haiku"` or `model: "sonnet"`, and `run_in_background: true`.
- The hand-off: in the Claude desktop app, propose a new session as a card. Use
  `start_session` with `initiation: "own_initiative"`, `context: "fresh"`,
  `title: <branch name>`, `prompt: "/builder <full plan path>"`, `background` (the goal
  of the plan and its full path, at least 80 characters), `use_worktree: true` and
  `branch_name: <branch name>`. The app adds a prefix and a suffix to the branch name.
  The builder creates the plan's branch in that worktree. The owner's click starts the
  session. The builder then moves itself to top level, so its reports do not come back
  to your session. Its close-out archives your session with its own. In the CLI, tell the owner to start a new session and run
  `/builder <full plan path>`.

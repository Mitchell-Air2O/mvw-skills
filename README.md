# mvw-skills

Mitchell Van Wagoner's agent skills. This repository is a Claude Code plugin marketplace.
Each plugin is a folder in `plugins/`. Each skill is one `SKILL.md` in the Agent Skills
format, so Codex and Gemini CLI can read it too.

## Plugin `workflow`

A change goes through four roles:

| Role | Kind | Does |
|---|---|---|
| `planner` | skill, `/planner` | Interviews the owner (the grill), lists the tasks, writes the plan in the main checkout, then hands off to a builder. |
| `builder` | skill, `/builder <plan path>` | Runs an approved plan in a fresh session. Groups the tasks into stages of about 100k tokens, picks the model and the effort of each stage, starts one worker per stage, reviews each diff, commits, keeps the plan current, and closes out. |
| `worker` | agent | Makes one stage from a brief and runs the build. It does not commit. |
| `reviewer` | skill `/reviewer`, and agent | Reviews all the work of a plan, runs a retro on its sessions, then asks if the work is ready to close out. |

The long form `/workflow:planner` applies only when another command has the short name.

The skills read the project values from the project instructions (`AGENTS.md`,
`CLAUDE.md`): the build command, the review checklist, the plan folder, the memory
folder, the declined-designs file, the retro queue, the branch rule and the merge
procedure.

## Install

### Claude Code

Claude Code v2.1.292 or later is necessary. The builder sets the effort of each
worker call, and older versions ignore it. The builder stops on an older version.
Run `claude update` first.

For one user:

```bash
claude plugin marketplace add Mitchell-Air2O/mvw-skills
claude plugin install workflow@mvw-skills
```

For every developer of a project, add this to the project's `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "mvw-skills": {
      "source": { "source": "github", "repo": "Mitchell-Air2O/mvw-skills" }
    }
  },
  "enabledPlugins": { "workflow@mvw-skills": true }
}
```

Claude Code offers the marketplace after the developer trusts the folder. Each developer
then installs the plugin one time on each PC, in the project folder:

```bash
claude plugin install workflow@mvw-skills --scope project
```

Without this step, the settings download the plugin but load no skill in `claude -p`. A
session that started before the install does not see the plugin's agents. Start a new
session after the install.

The context hook runs `python3`. Put `python3` on PATH. On Windows, a python.org install
can lack `python3`. Without `python3`, the hook fails and adds no line.

A background subagent call gets no hook line.
`context_report.py --session <session ID> --agent <agent ID>` prints the same line from
the transcripts.

Update:

```bash
claude plugin marketplace update mvw-skills
```

### Codex and Gemini CLI

Both tools read skills from `~/.agents/skills/`. Clone this repository one time, then
run the link script:

```bash
git clone https://github.com/Mitchell-Air2O/mvw-skills.git ~/mvw-skills
python3 ~/mvw-skills/scripts/link_skills.py
```

The script links each skill folder into `~/.agents/skills/`. On Windows the link is a
directory junction, which needs no admin rights. Elsewhere it is a symlink. The script
reports each link as `made`, `present` or `skipped`. It never replaces an entry that is
not a link to this clone. Run it again after a pull that adds a skill.

Update: `git pull` in the clone. The links then point to the new text.

The agents, the hook and the scripts are Claude Code only. In another tool, the builder
makes each stage itself or in that tool's own subagent. Assumption: Codex follows a
linked skill folder. This is not yet tested.

## Credits

The grill in `planner` adapts the `grilling` skill, and the retro in `reviewer` adapts
the `retro` skill, from [mattpocock/skills](https://github.com/mattpocock/skills)
(MIT, copyright Matt Pocock). See `LICENSE`.

## License

MIT. See `LICENSE`.

# Finding Unused Customizations

This skill lists the custom skills and subagents defined for **Claude Code** and reports the ones that were not used recently.
It reads definitions from `~/.claude` and the current project's `.claude`, and counts usage from Claude Code transcripts.

This skill works with Claude Code only. It does not read GitHub Copilot CLI logs.

## Usage

With no argument, it looks at the last 14 days.

```text
/finding-unused-customizations
```

Give a number of days to change the period.

```text
/finding-unused-customizations 30
```

Add `--projects-dir` to also scan transcripts from another environment, such as WSL when you run Claude Code on Windows.

```text
/finding-unused-customizations --projects-dir //wsl$/Ubuntu/home/<user>/.claude/projects
```

## Output

A table of unused definitions with their kind, name, scope (user or project), and a one-line description.
After the table, it notes broken definitions, invocations of names that no longer exist, and what the count cannot see.

It never deletes or disables anything. See [SKILL.md](SKILL.md) for details.

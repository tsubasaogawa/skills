---
name: finding-unused-customizations
description: List the custom skills and subagents defined for Claude Code (user-level ~/.claude and the current project's .claude), count how often each was used in recent Claude Code transcripts, and report the ones not used in the last N days (default 14) as a table with a one-line description of each. Use when the user asks which custom skills or agents have gone unused, are stale, or are candidates for cleanup. Claude Code only. Not for unused code, plugins, MCP servers, hooks, or other tools' logs, and it never deletes or disables anything.
disable-model-invocation: true
argument-hint: "[<days>] [--projects-dir <dir> ...]"
allowed-tools: Read, Bash(python3 -I:*), Bash(python -I:*)
metadata:
  version: 0.0.1
---

# Finding Unused Customizations

Find the custom skills and subagents that were not used recently. The only deliverable is the report in chat. Do not delete, move, disable, or edit any definition.

## Arguments

`$ARGUMENTS` takes the form `[<days>] [--projects-dir <dir> ...]`.

- `<days>`: length of the period in days.
  - Defaults to 14.
  - The period starts at local midnight `<days>` days before today.
  - If the value is not a positive integer, say so in one line and stop.
- `--projects-dir <dir>`: an extra directory of Claude Code transcripts to scan, repeatable. `~/.claude/projects` is always scanned.

If the user mentions running Claude Code in another environment too, ask whether to include that environment's `projects` directory and pass it with `--projects-dir`.
Examples of such an environment: Windows and WSL, or a second home directory.

## 1. Run the script

```bash
python3 -I ~/.claude/skills/finding-unused-customizations/scripts/find_unused.py --days <days> [--projects-dir <dir> ...]
```

Use `python -I` instead where `python3` does not exist. Run it from the project root, because project-level definitions are read from `./.claude`.

The script prints one JSON document:

- `definitions`: every agent (`*.md` in `agents/`) and skill (each directory in `skills/`) at the `user` and `project` scope, with `description`, `uses`, and `issues`
- `unmatched_invocations`: names that were invoked in the period but match no definition. Plugin-qualified names (`plugin:name`) are left out
- `period_utc`, `projects_dirs`, `missing_projects_dirs`, `transcript_files`: what was scanned

Usage is counted from three kinds of records in the period: Skill tool calls, Agent tool calls by `subagent_type`, and slash commands the user typed.
A skill matches by its directory name or its frontmatter `name`.

If the script fails, show the error as-is and stop. Do not fall back to grepping the transcripts by hand.

## 2. Build the table

List every definition whose `uses` is 0, agents first, then skills, each in alphabetical order. Use these columns, with headers in the user's language:

| Column | Content |
| --- | --- |
| Kind | agent or skill |
| Name | the directory name for a skill, the file name without `.md` for an agent |
| Scope | user or project |
| Description | what it does, in one short phrase in the user's language, written from the frontmatter `description` |

For a definition whose `description` is null, read the `issues` instead and say what is wrong in the Description cell, for example:
- that the directory has no `SKILL.md` and is probably not a skill.

If the issue says the file is unreadable, try reading it once more with Read; if that also fails, say it could not be read.

If nothing is unused, say so in one line instead of the table.

## 3. Report what else was found

After the table, add only the items below that apply, one line each:

- Definitions with `issues`, whether used or not:
  - unreadable files or broken links
  - a missing `SKILL.md`
  - a frontmatter that is not closed or whose closing `---` is indented
  - a frontmatter `name` that differs from the directory name
- `unmatched_invocations` that look like custom skills or agents that were renamed or removed.
  - Ignore built-in slash commands (`compact`, `model`, and so on) and built-in agents (`Explore`, `general-purpose`, and so on).
- `missing_projects_dirs`, if any

## 4. State the coverage

End with the period and the transcript directories that were scanned, then the blind spots, so the user does not delete something that is in use:

- Use outside Claude Code transcripts is not counted: other tools such as Codex or Copilot CLI, Claude Code on other machines, and cloud sessions
- A skill followed by reading its `SKILL.md` directly, without the Skill tool or a slash command, is not counted
- Claude Code deletes transcripts older than `cleanupPeriodDays` (30 days by default). If `<days>` is longer than that setting, older use may already be gone

## What to avoid

- Deciding for the user that something should be deleted. Report the facts; the user decides
- Listing used definitions in the table, or listing built-in agents and plugin skills as custom ones
- Saying a definition is unused when its file could not be read and the reason is unclear. Say it could not be checked

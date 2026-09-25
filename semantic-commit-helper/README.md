# Semantic Commit Helper Skill

This repository contains the `semantic-commit-helper` skill for the AI Agent.
This skill assists users in creating commit messages that adhere to the Conventional Commits specification, with as few round-trips as possible.

## Example

```console
> /semantic-commit-helper

✦ Which commit message fits best?
  1. docs: add system architecture diagram
  2. docs: visualize Lambda-based request flow in README
  3. feat: ship architecture.svg as a project asset
> 1

✦ Committed: docs: add system architecture diagram
```

Quick mode:

```console
> /semantic-commit-helper --quick

✦ Committed: fix(parser): handle empty input without panicking
```

## Features

- **Session-aware**: If the session already contains the edits being committed, uses that history instead of reading `git diff`.
- **Single-shot Analysis**: Otherwise reads status, stat, and diff in one command. Large diffs are summarized instead of read in full.
- **One Question at Most**: Proposes 3 complete commit message candidates and commits the chosen one. No separate motivation question, no confirmation step.
- **Auto-skip for Obvious Changes**: Typo fixes, dependency bumps, renames, and similar changes are committed without asking.
- **Quick Mode**: `--quick` (or `--fast`) skips every question and commits immediately.
- **Conventional Commits**: Generates messages following the standard format (`type(scope): subject`).

## Usage

1.  Stage your changes with `git add`.
2.  Ask the agent:
    > "Commit these changes"
    > "/semantic-commit-helper --quick"
    > "/semantic-commit-helper japanese"
3.  Pick a candidate if asked. The agent commits and stops.

## Arguments

| Argument | Effect |
|---|---|
| `--quick`, `--fast` | Skip all questions and commit immediately |
| `japanese`, `english`, ... | Language of the commit message (default: English) |

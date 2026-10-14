# Branch TL;DR

This skill summarizes a branch or pull request's **committed diff** against its default branch in exactly three concise bullet points.

## Usage

With no argument, it summarizes the current branch.

```text
/branch-tldr
```

You can also specify a branch name or PR number.

```text
/branch-tldr feature/add-search
/branch-tldr 123
```

Use `--expertise` to change the reader's expertise level for a single run.

```text
/branch-tldr --expertise high
/branch-tldr 123 --expertise low
```

## Configuration

Set the maximum line length, writing style, and reader's expertise level (`high`, `medium`, or `low`; default `medium`) in `~/.config/branch-tldr/config.toml`. The skill uses its defaults when the file does not exist.

This skill is not for creating commit messages, reviewing code quality, or summarizing only uncommitted changes. See [SKILL.md](SKILL.md) for details.

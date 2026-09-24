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

## Configuration

Set the maximum line length and writing style in `~/.config/branch-tldr/config.toml`. The skill uses its defaults when the file does not exist.

This skill is not for creating commit messages, reviewing code quality, or summarizing only uncommitted changes. See [SKILL.md](SKILL.md) for details.

# PR Branch Composition Check

This skill mechanically verifies that a pull request contains commits only from the specified parent branches or PRs. It is useful for finding unintended commits in stacked PRs.

## Usage

Specify the target PR and its permitted parent branches or PRs.

```text
Check that this PR contains only commits from feature/auth, #42, and #43.
Check whether PR #100 contains commits other than those in #98 and #99.
```

Explicit input in the conversation takes precedence. You can also ask it to use parent PRs listed in the PR description.

## What it checks

- Retrieves the target PR's commits
- Compares them with the commits from each specified branch or PR
- Identifies unmatched commits and classifies them as expected or anomalous

This is not a general code review of code quality or diff content. See [SKILL.md](SKILL.md) for the complete workflow and constraints.

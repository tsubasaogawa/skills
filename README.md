# skills

A collection of personal GitHub Copilot CLI skills. Each directory is a self-contained skill; its `SKILL.md` defines the trigger conditions and workflow.

## Skills

| Skill | Description |
| --- | --- |
| [ai-credit-efficient-review](ai-credit-efficient-review/) | Review efficiently by focusing AI Credit on material risks |
| [branch-tldr](branch-tldr/) | Summarize a branch or PR's committed changes in three points |
| [hacker-news-digest](hacker-news-digest/) | Create a Japanese digest of yesterday's popular Hacker News stories |
| [japanese-tech-writing](japanese-tech-writing/) | Create and revise natural, clear Japanese technical writing |
| [pr-branch-composition-check](pr-branch-composition-check/) | Verify that a PR contains commits only from specified branches or PRs |
| [prompt-feedback](prompt-feedback/) | Provide good / more / next action feedback on conversation prompts |
| [resume-improver](resume-improver/) | Restructure Japanese resumes while preserving supporting evidence |
| [semantic-commit-helper](semantic-commit-helper/) | Create a Conventional Commits message and commit staged changes |
| [session-stocker](session-stocker/) | Save a conversation as a Markdown note in an artifacts directory |
| [skill-fork-sync](skill-fork-sync/) | Interactively apply upstream updates to a customized forked skill |
| [tf-destroy-plan-inverter](tf-destroy-plan-inverter/) | Desk-check a Terraform destroy diff as an equivalent create plan |

## Installation

Install a single skill for GitHub Copilot in the current repository:

```console
gh skill install tsubasaogawa/skills branch-tldr --agent github-copilot
```

Install every skill:

```console
gh skill install tsubasaogawa/skills --all --agent github-copilot
```

The default installation scope is `project`. Add `--scope user` to make a skill available across your local projects:

```console
gh skill install tsubasaogawa/skills branch-tldr --agent github-copilot --scope user
```

## Usage

Skills activate when a request matches the description in their `SKILL.md`, for example:

```text
Summarize this branch's changes in three lines.
Commit my staged changes.
Convert this destroy plan into an equivalent create plan.
```

See each skill's `README.md` for its arguments, configuration, and examples.
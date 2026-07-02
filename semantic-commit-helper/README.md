# Semantic Commit Helper Skill

This repository contains the `semantic-commit-helper` skill for the AI Agent.
This skill assists users in creating commit messages that adhere to the Conventional Commits specification.

## Example

```console
✦ I will activate the semantic-commit-helper skill to assist with generating a high-quality commit message and finalizing the commit.

✦ I'll check the staged changes with git status and git diff --staged to understand the updates.

✦ What is the primary motivation or reason for adding this system architecture diagram?
> Because the README lacked even a simple configuration diagram, making it difficult to grasp the system overview.

✦ I have drafted the following commit message based on your input:

   1 docs: add system architecture diagram
   2
   3 Add `architecture.svg` to visualize the system structure (Client, API Gateway, Lambda, Embedded CSV).
   4 This addresses the lack of a simple architecture diagram for the documentation.

  Shall I proceed with the commit?

✦ I have successfully committed the changes.

   1 [main 5830c0c] docs: add system architecture diagram
   2  1 file changed, 50 insertions(+)
   3  create mode 100644 architecture.svg
```

## Features

- **Automated Analysis**: Analyzes staged changes (`git diff --staged`) to understand the "what".
- **Intent Gathering**: Asks the user for the "why" to ensure meaningful commit messages.
- **Conventional Commits**: Generates messages following the standard format (`type(scope): subject`).
- **Interactive Workflow**: Guides the user through staging, reviewing, and committing changes.

## Usage

To use this skill with the Agent:

1.  Ensure you are in this repository or have the skill configured in your agent's path.
2.  When you want to commit changes, simply ask the agent:
    > "Commit these changes"
    > "Help me commit"
3.  The agent will activate the `semantic-commit-helper` skill and guide you through the process.

## Skill Definition

The skill definition matches the prompt located in
  - `~/.gemini/skills/semantic-commit-helper/SKILL.md` (Gemini CLI)
  - `~/.claude/skills/semantic-commit-helper/SKILL.md` (Claude Code)
  - ...


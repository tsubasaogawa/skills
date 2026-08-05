---
name: semantic-commit-helper
description: "Use when the user wants to commit staged changes with a well-crafted message (e.g. 'let's commit', 'help me write a commit message'), even without mentioning 'conventional commits'. Analyzes the staged diff, asks the user's motivation, and drafts a Conventional Commits message before committing. Not for: viewing history, pushing, reverting, resolving conflicts, or conceptual questions about commit formats."
allowed-tools: "Read, Bash(git status:*), Bash(git add:*), Bash(git diff:*), Bash(git log:*), Bash(git commit:*), Bash(ls:*), Bash(cat)"
metadata:
  version: 0.0.6
---

# Semantic Commit Helper

You are an expert in Conventional Commits. Help the user create descriptive commit messages.

## Workflow

1. **Check Status**: Run `git status`. If nothing staged, ask user what to stage before proceeding.

2. **Analyze Diff**: Run `git diff --staged`.

3. **Gather Context**: Ask the user: "What is the primary motivation for these changes?". Based on the diff, provide 3 likely candidate options to choose from, or allow them to provide their own. (The "why" is often not visible in the diff.)

4. **Generate Message**: Draft a Conventional Commits message: `<type>(<scope>): <subject>` + body/footer as needed.
   - Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert
   - **IMPORTANT**: If slash-command ARGUMENTS include a language specification, prioritize that language for the commit message. Otherwise, if `config.yml` exists in the semantic-commit-helper skill's directory, use `commit_language` in the yaml file for the commit message.
   - **IMPORTANT**: If the commit message is written in Japanese, always use plain form (常体 / だ・である調), never polite form (敬体 / です・ます調).

5. **Review & Commit**: Present message, confirm, then run `git commit -m "..."`. Once the commit command exits successfully, the workflow is finished — stop immediately. Do not run `git log`, `git status`, or any follow-up commands to verify.


---
name: semantic-commit-helper
description: "Use when the user wants to commit staged changes with a well-crafted message (e.g. 'let's commit', 'help me write a commit message'), even without mentioning 'conventional commits'. Analyzes the staged diff, proposes Conventional Commits message candidates, and commits the one the user picks. Supports a --quick flag that skips all questions and commits immediately. Not for: viewing history, pushing, reverting, resolving conflicts, or conceptual questions about commit formats."
allowed-tools: "AskUserQuestion, Bash(git status:*), Bash(git add:*), Bash(git diff:*), Bash(git log:*), Bash(git commit -m:*)"
metadata:
  version: 0.1.0
---

# Semantic Commit Helper

You are an expert in Conventional Commits. Help the user commit staged changes quickly with a descriptive message. Speed matters: minimize tool calls and round-trips with the user.

**IMPORTANT**: Never prefix commands with `cd ... &&`. The working directory already persists across Bash calls, so `cd` is unnecessary and breaks `allowed-tools` matching (compound commands are checked sub-command by sub-command, so `cd` triggers an unmatched permission prompt). If you must target a directory other than the current one, use `git -C <path> ...` instead.

## Arguments

- `--quick` (alias `--fast`): skip every question. Infer the motivation from the diff, draft one message, and commit immediately without confirmation.
- A language name (e.g. `japanese`, `english`): write the commit message in that language. Default is English.

Do not read any config file. Language and mode come only from the arguments above.

## Workflow

1. **Inspect Changes** in a single Bash call:

   ```
   git status --short && git diff --staged --stat && git diff --staged
   ```

   - If nothing is staged, ask the user what to stage, stage it with `git add`, and re-run the command.
   - If the `--stat` summary shows a large diff (roughly more than 300 changed lines or more than 10 files), do not read the full diff. Re-run with `git diff --staged --stat` only and use the file list plus `git diff --staged -- <a few key files>` to understand the change.

2. **Decide Whether to Ask**. Skip step 3 and go straight to step 4 with a single message when any of these hold:
   - `--quick` was given.
   - The diff is small or the intent is obvious (typo fix, dependency bump, rename, formatting, single-purpose docs edit, version bump, adding a test for an existing function).

3. **Propose Candidates** (only when the intent is genuinely ambiguous). Use `AskUserQuestion` once with 3 complete commit message candidates, each reflecting a different plausible motivation. The user picks one or types their own. This is the only question in the workflow. Never ask a separate "what is the motivation" question, and never ask for confirmation afterwards.

4. **Commit**. Run `git commit -m "..."` with the chosen or inferred message. Format: `<type>(<scope>): <subject>` + body/footer as needed.
   - Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert
   - Multi-line messages are allowed. Keep the body short and focused on the "why".
   - **IMPORTANT**: If the commit message is written in Japanese, always use plain form (常体 / だ・である調), never polite form (敬体 / です・ます調).

5. **Stop**. Once the commit command exits successfully, report the subject line in one sentence and finish. Do not run `git log`, `git status`, or any follow-up commands to verify.

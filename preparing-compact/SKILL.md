---
name: preparing-compact
description: Takes the next task and writes summarization instructions for /compact to a file. Use as "/preparing-compact <task>".
disable-model-invocation: true
---

# Preparing arguments for /compact

`$ARGUMENTS` is the task to work on after compacting. Read this conversation and write summarization instructions that keep the context needed for that task.

Write the instructions to a file. When the user runs `/compact` without arguments, the PreCompact hook
(`scripts/inject_compact_instructions.py`) passes the file to the summarizer as instructions and deletes it after use.
A skill cannot run `/compact`, so the user runs it.

## Arguments

- A task is given: treat it as the next task
- Empty: ask what to do next and stop. Do not guess from the conversation

## What to keep

Include only what relates to the next task. Leave out anything unrelated, even if it came up in the conversation.

- The goal of the next task and its completion criteria
- Decisions made in this conversation, and the reasons for them
- File paths, ticket keys, branch names, and commands for the task
- Open questions and items awaiting the user's decision
- Feedback and preferences from the user (writing style, how to proceed)
- Approaches that were tried and failed, and why (to avoid repeating them)

## What to drop

- Full tool output and file contents (keep only conclusions, and line numbers if needed)
- History of completed work unrelated to the next task

## Writing the file

1. Run `echo "$CLAUDE_CODE_SESSION_ID"` with Bash to get the session ID. If it is empty, do not write anything; say so and stop
2. Use the Write tool to write the instructions to `<vault root>/.claude/compact-instructions/<session ID>.md`. Overwrite it if it already exists
3. In the chat, say only that the file was written and that the user should run `/compact` without arguments. Do not repeat the instructions

## How to write the instructions

- Write only the instructions. No `/compact ` prefix, preamble, or closing remarks
- Write proper names (paths, keys, commands) exactly as they appeared in the conversation. Be specific so they are not abbreviated during summarization
- Do not add facts that did not appear in this conversation
- Do not create or modify any file other than the output file. Do not run `/compact`

---
name: session-stocker
description: Summarize useful knowledge from the current conversation and save it as a Markdown note in the directory configured by `config.toml` (`artifacts.directory`, default: `/mnt/c/Users/t_ogawa/Documents/documents/12_Artifacts/`). Use this skill whenever the user asks to stock, archive, preserve, save, memoize, or record the current session, especially when they say phrases like `このセッションをストックして`, want a reusable note from the conversation, or ask to write a session summary into an artifacts folder.
---

# Session Stock

Turn the current session into a reusable Markdown artifact and save it to the directory configured by `config.toml`.

## Goal

Capture the conversation in a form the user can revisit later. Focus on durable takeaways rather than chat-like narration.

## When to use this skill

Use this skill when the user wants to preserve the current session as a note, especially if they want the result written to disk for later reference.

Typical triggers include:
- `このセッションをストックして`
- `この会話を残して`
- `今回の内容を artifacts に保存して`
- `セッションの知見をメモ化して`

## Output requirements

Create one Markdown file at:

`<artifacts-directory>/<YYYYMMDD>_<session-summary>.md`

Resolve `<artifacts-directory>` from `config.toml` using `artifacts.directory`.
If `artifacts.directory` is missing, fall back to `/mnt/c/Users/t_ogawa/Documents/documents/12_Artifacts/`.

The file must contain these sections in this order:

```md
# <session-summary>

## 概要

## 知見

## 参考情報
```

## Writing guidance

### 1. Decide the session summary

Create a short summary phrase from the conversation.

Good summaries are:
- short and specific
- understandable without the full chat log
- suitable for a filename

Examples:
- `Terraform module 分割方針`
- `Python 集計スクリプト改善`
- `GitHub Actions 失敗原因調査`

### 2. Build a safe filename

- Prefix the filename with the current date in `YYYYMMDD` format.
- Convert the summary into a filename-safe form.
- Replace spaces with `-`.
- Remove or replace characters that are unsafe in filenames, such as `/`, `\\`, `:`, `*`, `?`, `"`, `<`, `>`, and `|`.
- Keep the summary readable after sanitizing.

If a file with the same name already exists, append `-2`, `-3`, and so on instead of overwriting it.

### 3. Write the content

#### `概要`

Write a short overview of what the session accomplished. Keep it compact and outcome-oriented.

#### `知見`

List the important learnings, decisions, trade-offs, or implementation notes that would help someone reuse the result later. Prefer bullets when there are multiple items.

Include:
- conclusions that were reached
- constraints or assumptions that mattered
- patterns worth repeating
- pitfalls or caveats discovered during the session

#### `参考情報`

Record concrete references from the session that may be useful later.

Examples:
- file paths
- command names
- tool names
- issue or PR numbers
- external URLs mentioned during the work

If a category has no relevant items, write `- なし` instead of leaving the section empty.

## Execution steps

1. Review the current conversation and extract durable information.
2. Generate the session summary.
3. Read `config.toml` and resolve `artifacts.directory`.
4. Ensure the resolved artifacts directory exists. Create it if necessary.
5. Create the final Markdown content.
6. Save the file using the required naming rule.
7. Tell the user the saved path and briefly summarize what was captured.

## Quality bar

Before saving, check that:
- the file is actually written to disk
- the filename matches the required pattern
- the content is concise and useful later
- the `知見` section contains real takeaways, not a transcript rewrite
- the `参考情報` section contains concrete references or `- なし`

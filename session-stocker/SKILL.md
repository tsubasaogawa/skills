---
name: session-stocker
description: Summarize useful knowledge from the current conversation and save it as a Markdown note in the directory configured by `config.toml` (`artifacts.directory`). Use this skill whenever the user asks to stock, archive, preserve, save, memoize, or record the current session, especially when they say phrases like `このセッションをストックして`, want a reusable note from the conversation, or ask to write a session summary into an artifacts folder.
---

# Session Stock

Turn the current session into a reusable Markdown artifact and save it to the directory configured by `config.toml`.

## Goal

Capture the conversation in a form the user can revisit later. Preserve the actual exchange verbatim rather than compressing it into a summary — durable takeaways (`知見`) are an optional add-on, not the primary content.

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

The file must always contain these sections in this order:

```md
# <session-summary>

## 概要

## 会話内容
```

`知見` is optional. Only add it after saving, once the user has confirmed they want it (see Execution steps). When present, it goes right after `会話内容`:

```md
## 知見
```

If the session includes one or more relevant URLs, append this optional section last:

```md
## 参考情報
- https://example.com/reference
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

#### `会話内容`

This is the core of the artifact: a verbatim, turn-by-turn transcript of what the user and the assistant actually said, in order. Do not summarize or condense it — the whole point of this section is to preserve the conversation as it happened, not a distilled version of it.

- Render each turn as a `**User:**` or `**Assistant:**` block followed by that turn's text, in the order the turns occurred.
- Use the actual message text the user and assistant exchanged, not a paraphrase.
- Leave out tool-call/tool-result noise (function calls, raw command output, intermediate tool payloads) — keep only what the user and the assistant actually said to each other. Local-command output and system-reminder tags are not part of the conversation and should also be left out.
- If the session is extremely long, it's fine to include the whole thing; do not truncate for length unless the user asks you to.

#### `知見`

Optional. List the important learnings, decisions, trade-offs, or implementation notes that would help someone reuse the result later. Prefer bullets when there are multiple items.

Include:
- conclusions that were reached
- constraints or assumptions that mattered
- patterns worth repeating
- pitfalls or caveats discovered during the session

Only write this section when the user has confirmed they want it (see Execution steps) — otherwise leave it out entirely.

#### `参考情報`

Record only relevant URLs from the session that may be useful later.

Do not include file paths, command names, tool names, issue or PR numbers, or any other non-URL references.

If there are no relevant URLs, omit the entire `参考情報` section.

## Execution steps

1. Review the current conversation and reconstruct the verbatim turn-by-turn transcript (`会話内容`), and generate the session summary.
2. Read `config.toml` and resolve `artifacts.directory`.
3. Ensure the resolved artifacts directory exists. Create it if necessary.
4. Create the Markdown content with `概要` and `会話内容`, adding `参考情報` only when relevant URLs were actually mentioned. Do not include `知見` yet.
5. Save the file using the required naming rule.
6. Tell the user the saved path and briefly summarize what was captured.
7. Ask the user whether they want to add a `知見` section, e.g. 「知見を追加しますか？」. If they say yes, extract the durable learnings and append the `知見` section to the already-saved file (right after `会話内容`, before `参考情報` if present). If they decline or don't respond, leave the file as is.

## Quality bar

Before saving, check that:
- the file is actually written to disk
- the filename matches the required pattern
- the `会話内容` section is a verbatim transcript of the actual exchange, not a summary or paraphrase
- tool-call noise, raw command output, and system-reminder content are excluded from `会話内容`
- the `知見` section is only present if the user explicitly asked for it, and if so, contains real takeaways rather than a repeat of the transcript
- the `参考情報` section appears only when relevant URLs exist
- when `参考情報` is present, it contains URLs only

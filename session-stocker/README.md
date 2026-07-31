# session-stocker-skill

This skill saves the current conversation as a Markdown note in an artifacts folder, keeping the actual exchange verbatim rather than compressing it into a summary.

## Overview

This skill turns an in-progress session into something you can revisit later. The core of the saved note is a verbatim transcript of the conversation; a short overview, a durable-knowledge section, and reference links can be added around it.

The output directory is configured through `config.toml`, which always lives at `~/.config/session-stocker/config.toml` — not inside this repository.

```toml
[artifacts]
directory = "/path/to/your/artifacts"
use_obsidian_cli = false
```

`use_obsidian_cli` selects how the note is written, and also changes what `artifacts.directory` means. The content is identical either way. A missing key is treated as `false`.

- `false` — `artifacts.directory` is an absolute filesystem path, and the file is written directly there.
- `true` — `artifacts.directory` is a folder **relative to the vault root** (empty means the vault root), and the note is created through the [Obsidian CLI](https://help.obsidian.md/cli) (Obsidian must be running). Useful when the vault sits somewhere the shell can't write to conveniently — a Windows path used from WSL, for example — and it also gets the note indexed by Obsidian right away. Which vault is used comes from `vault_name`, or, if that's empty, whichever vault Obsidian currently has focused.

### Setup

```bash
mkdir -p ~/.config/session-stocker
cp config.toml.template ~/.config/session-stocker/config.toml
# edit ~/.config/session-stocker/config.toml and set artifacts.directory
```

## When to use it

Use this skill when you want to preserve the contents of a conversation for later reference, especially when you want the result saved to disk as a Markdown file.

Typical triggers:

- `このセッションをストックして`
- `この会話を残して`
- `今回の内容を artifacts に保存して`
- `セッションの知見をメモ化して`

## Generated file

The generated file uses the following format:

`<artifacts-directory>/<YYYYMMDD>_<HHMM>_<session-summary>.md`

Here, `<artifacts-directory>` is `artifacts.directory` from `~/.config/session-stocker/config.toml`.

### Filename rules

- Prefix the filename with the current date and time in `YYYYMMDD_HHMM` format (24-hour clock, local time)
- Use a short summary of the conversation in the filename
- Spaces are allowed in the title portion and are kept as-is (not replaced with `-` or `_`)
- Remove or replace unsafe filename characters such as `/`, `\\`, `:`, `*`, `?`, `"`, `<`, `>`, and `|`
- With `use_obsidian_cli = true`, `#`, `^`, `[`, and `]` are dropped as well, since Obsidian rejects them in note names
- Keep the sanitized filename readable

If a file with the same name already exists, do not overwrite it. Append `-2`, `-3`, and so on instead.

### How to choose the summary name

The summary should be short, specific, and understandable without reading the full conversation.

Examples:

- `Terraform module 分割方針`
- `Python 集計スクリプト改善`
- `GitHub Actions 失敗原因調査`

## Markdown output format

The saved Markdown must always include the following sections in this order:

```md
# <session-summary>

## 概要

## 会話内容
```

`知見` is optional: it's only added after the file is saved, once the user has confirmed they want it. When present, it goes right after `会話内容`:

```md
## 知見
```

If the session contains one or more relevant URLs, append this optional section last:

```md
## 参考情報
- https://example.com/reference
```

### Purpose of each section

#### `概要`

Summarize what the session accomplished in a short, outcome-oriented way.

#### `会話内容`

A verbatim, turn-by-turn transcript of what the user and the assistant actually said, in order — not a summary or paraphrase. Each turn is rendered as a `**User:**` or `**Assistant:**` block. Tool-call/tool-result noise, raw command output, and system-reminder content are excluded; only what the two parties actually said to each other is kept.

#### `知見`

Optional. Record learnings and decisions that will be useful later. Use bullet points when there are multiple items.

Include:

- conclusions that were reached
- important assumptions or constraints
- patterns worth reusing
- pitfalls or caveats discovered during the session

Only included when the user explicitly asks for it after the file has been saved (see Execution flow).

#### `参考情報`

Record only relevant URLs that may be useful later.

Do not include file paths, command names, tool names, issue or PR numbers, or any other non-URL references.

If there are no relevant URLs, omit the entire `参考情報` section.

#### Links to other notes

This skill doesn't search for related notes on its own. But if a section ends up referencing another note that already lives in the stock directory, the link syntax depends on whether the stock is an Obsidian vault. `use_obsidian_cli = true` already settles that; otherwise the Git repository root for `artifacts.directory` is resolved and checked for a `.obsidian` directory directly under it.

- Obsidian vault detected: use wiki link syntax, `[[Note Title]]` (no `.md` extension; `[[Note Title|Display Text]]` for an alias).
- Otherwise: use a normal Markdown relative link, `[Note Title](relative/path.md)`.

This only applies to links between notes — `参考情報` stays URL-only.

## Execution flow

This skill follows the steps below:

1. Reconstruct the verbatim turn-by-turn transcript (`会話内容`) and decide on a short summary for the session
2. Read `~/.config/session-stocker/config.toml` and resolve `artifacts.directory` and `use_obsidian_cli`
3. Build the Markdown content with `概要` and `会話内容`, adding `参考情報` only when relevant URLs were mentioned (no `知見` yet)
4. Save the note — directly into the output directory, or through the Obsidian CLI when `use_obsidian_cli = true`
5. Tell the user the saved path and briefly summarize what was captured
6. Ask the user whether they want a `知見` section added; if they agree, add it to the saved note

### Writing through the Obsidian CLI

When `use_obsidian_cli = true`, the note is created by `scripts/obsidian_stock.py`, which wraps the `obsidian` CLI.

The CLI takes note bodies as a `content=` argument in which `\n` and `\t` are expanded and a backslash cannot be escaped, so passing a transcript through it directly would silently corrupt Windows paths, regexes, and code containing `\n`. The script avoids that: backslashes are swapped for a private-use placeholder before the note is created, restored inside Obsidian afterwards, and the stored note is read back and compared against the original. A mismatch is reported as an error rather than passed off as a successful stock.

The script also resolves the vault to use (`vault_name`, or whichever vault Obsidian currently has focused if that's empty), treats `artifacts.directory` as the vault-relative folder, applies the naming rule, and avoids overwriting an existing note.

```bash
python3 scripts/obsidian_stock.py create --title "<session summary>" --body /tmp/session-stock-body.md
python3 scripts/obsidian_stock.py overwrite --path "<vault-relative path>" --body /tmp/session-stock-body.md
```

If Obsidian isn't running, the CLI isn't installed, `vault_name` doesn't match any known vault, or no vault could be detected as active, the error is surfaced and nothing is written elsewhere.

## Quality bar

Before saving, make sure at least the following are true:

- the file is actually written to disk
- the filename follows the required pattern
- the `会話内容` section is a verbatim transcript, not a summary or paraphrase, and excludes tool-call noise
- the `知見` section is only present when the user explicitly asked for it
- the `参考情報` section appears only when relevant URLs exist
- when `参考情報` is present, it contains URLs only

## Why this skill is useful

This skill turns an ephemeral chat into a reusable artifact. By preserving investigation results, decisions, and implementation notes as artifacts, it becomes much easier to revisit the same topic later.

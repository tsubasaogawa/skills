---
name: session-stocker
description: Summarize useful knowledge from the current conversation and save it as a Markdown note in the directory configured by `config.toml` (`artifacts.directory`). Use this skill whenever the user asks to stock, archive, preserve, save, memoize, or record the current session, especially when they say phrases like `このセッションをストックして`, want a reusable note from the conversation, or ask to write a session summary into an artifacts folder.
---

# Session Stock

Turn the current session into a reusable Markdown artifact and save it to the directory configured by `config.toml`.

## Goal

Capture the conversation in a form the user can revisit later. Preserve the actual exchange verbatim rather than compressing it into a summary — durable takeaways (`知見`) are an optional add-on, not the primary content. Pass `simplify=true` in the invoking ARGUMENTS to condense the transcript into a summary instead; this is off by default (see [Simplify mode](#simplify-mode)).

## When to use this skill

Use this skill when the user wants to preserve the current session as a note, especially if they want the result written to disk for later reference.

Typical triggers include:
- `このセッションをストックして`
- `この会話を残して`
- `今回の内容を artifacts に保存して`
- `セッションの知見をメモ化して`

## Configuration

The config file always lives at `~/.config/session-stocker/config.toml`, regardless of where this skill itself is installed:

```toml
[artifacts]
directory = "/path/to/your/artifacts"
use_obsidian_cli = false
vault_name = ""
```

If that file doesn't exist, stop and tell the user to create it (they can copy `config.toml.template` from the skill directory to `~/.config/session-stocker/config.toml` and fill in `artifacts.directory`) rather than guessing a directory or writing anywhere else.

`use_obsidian_cli` decides **how** the note is written, and also changes what `artifacts.directory` means. The content rules are identical either way. Treat a missing key as `false`.

- `false` — `artifacts.directory` is an absolute filesystem path. Write the file straight there with your normal file-writing tool.
- `true` — `artifacts.directory` is a folder **relative to the vault root** (leave it empty to save at the vault root), and the write is handed to the Obsidian CLI as described in [Stocking through the Obsidian CLI](#stocking-through-the-obsidian-cli). This matters when the vault lives somewhere the shell can't write to conveniently (for example a Windows path used from WSL), and it lets Obsidian index the note immediately.

`vault_name` names which vault to save into when `use_obsidian_cli = true`. Leave it empty to use whichever vault Obsidian currently has focused — the bundled script asks the CLI for the active vault when no name is configured. Set it explicitly when you want a specific vault regardless of what's currently open in Obsidian.

## Plain mode

By default, the stock target is the full conversation (`会話内容`, verbatim turns from both the user and the assistant). Plain mode narrows that down to **assistant output only** — every assistant utterance in the session, in order, with user turns left out entirely.

Plain mode is on only when the slash-command ARGUMENTS that invoked this skill literally contain `plain=true` (e.g. `/session-stocker plain=true`). A natural-language request like「plain で保存して」does not trigger it — only the explicit ARGUMENTS flag does. This check is independent of the vault-name override described below; both can apply at once.

When plain mode is on, the file uses `## 回答内容` instead of `## 会話内容` (see Output requirements and Writing guidance) — the two never appear together in the same note.

## Simplify mode

By default, `会話内容` (or `回答内容` in plain mode) is a verbatim, turn-by-turn transcript. Simplify mode replaces that with a condensed summary of what was discussed/done instead — still faithful to what happened, but not word-for-word.

Simplify mode is on only when the slash-command ARGUMENTS that invoked this skill literally contain `simplify=true` (e.g. `/session-stocker simplify=true`). A natural-language request like「内容を要約して保存して」does not trigger it — only the explicit ARGUMENTS flag does. Default is `simplify=false` (verbatim), matching the skill's existing behavior.

Simplify mode is independent of [Plain mode](#plain-mode) — the two combine freely:

| `plain` | `simplify` | Section | Content |
|---|---|---|---|
| false (default) | false (default) | `会話内容` | verbatim, both parties |
| false | true | `会話内容` | summarized, both parties |
| true | false | `回答内容` | verbatim, assistant only |
| true | true | `回答内容` | summarized, assistant only |

## Output requirements

Create one Markdown file at:

`<artifacts-directory>/<YYYYMMDD>_<HHMM>_<session-summary>.md`

Resolve `<artifacts-directory>` from `~/.config/session-stocker/config.toml` using `artifacts.directory` (see Configuration above).

The file must always contain these sections in this order:

```md
# <session-summary>

## 概要

## 会話内容
```

In plain mode (see [Plain mode](#plain-mode)), use `## 回答内容` in place of `## 会話内容` — never both:

```md
# <session-summary>

## 概要

## 回答内容
```

`知見` is optional. Only add it after saving, once the user has confirmed they want it (see Execution steps). When present, it goes right after `会話内容` (or `回答内容` in plain mode):

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

- Prefix the filename with the current date and time in `YYYYMMDD_HHMM` format (24-hour clock, local time).
- Convert the summary into a filename-safe form.
- Spaces are allowed in the title portion — do not replace them with `-` or `_`.
- Remove or replace characters that are unsafe in filenames, such as `/`, `\\`, `:`, `*`, `?`, `"`, `<`, `>`, and `|`.
- With `use_obsidian_cli = true`, also drop `#`, `^`, `[`, and `]` — Obsidian rejects them in note names.
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
- When [simplify mode](#simplify-mode) is on (`simplify=true`), write a condensed summary of the exchange instead — cover the key turns, decisions, and outcomes, but do not preserve exact wording. This does not apply when simplify is off (default), where the verbatim rule above still governs.

#### `回答内容` (plain mode only)

Used instead of `会話内容` when [plain mode](#plain-mode) is on. Contains every assistant utterance from the session, in order, with user turns left out entirely.

- Use the actual assistant message text, verbatim — do not summarize or paraphrase, same as `会話内容`.
- Leave out tool-call/tool-result noise, raw command output, and system-reminder content, same exclusion rule as `会話内容`.
- Separate consecutive assistant utterances so the boundaries stay legible when read back — a `**Assistant:**` label per turn or a `---` divider both work. Don't use `**User:**` labels; there's nothing to attribute to the user in this section.
- When [simplify mode](#simplify-mode) is on (`simplify=true`), write a condensed summary of the assistant's output instead — cover the key points and outcomes, but do not preserve exact wording. This does not apply when simplify is off (default), where the verbatim rule above still governs.

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

### 4. Linking to other notes (Obsidian-aware)

This skill doesn't go looking for related notes to link on its own — this rule only matters if a section ends up referencing another note that already lives in the same stock directory (for example, if the user asks you to link a related past note, or `知見` naturally calls one out).

When that happens, decide the link style by whether the stock is Obsidian-managed:

- `use_obsidian_cli = true` already answers this — the stock is Obsidian-managed, no further detection needed.
- Otherwise, resolve the Git repository root for `artifacts.directory` (e.g. `git -C <artifacts-directory> rev-parse --show-toplevel`) and check whether a `.obsidian` directory exists directly under that root. If it does, the stock is Obsidian-managed.

Then pick the syntax:

- Obsidian-managed: use Obsidian's wiki link syntax, `[[Note Title]]` (no `.md` extension; use `[[Note Title|Display Text]]` if you need an alias).
- Not Obsidian-managed (not a Git repo, or no `.obsidian` at the root): use a normal Markdown relative link, `[Note Title](relative/path.md)`.

This only governs links between notes in the stock. `参考情報` stays URL-only regardless of this detection.

## Stocking through the Obsidian CLI

Only relevant when `use_obsidian_cli = true`. The Obsidian CLI drives a running Obsidian instance, so the note lands in the vault the same way a manually created note would. See `rules/obsidian.md` for the CLI's general syntax if you need ad-hoc commands.

Do not build the `obsidian create` call by hand. The CLI expands `\n` and `\t` inside `content=` and offers no way to escape a backslash, so a transcript containing Windows paths, regexes, or code with `\n` in a string would be silently corrupted — exactly the fidelity this skill exists to protect. Use the bundled script instead, which routes the body through a placeholder, restores it inside Obsidian, and reads the note back to confirm it matches:

```bash
python3 <skill-dir>/scripts/obsidian_stock.py create \
  --title "<session summary>" \
  --body /tmp/session-stock-body.md
```

Write the Markdown body (everything from `# <session-summary>` down) to a temp file first, then pass it with `--body`. The script resolves the vault (from `vault_name`, or the currently focused vault if that's empty), treats `artifacts.directory` as the vault-relative folder, adds the `YYYYMMDD_HHMM` prefix, sanitizes the title, picks a collision-free `-2`/`-3` name, and prints the vault name and note path it used. Report that path to the user.

**Explicit vault override**: if the user's request or slash-command ARGUMENTS name an Obsidian vault to save into (e.g. "Work vault に保存して"), prioritize that vault for this run by passing `--vault "<name>"` — same pattern as `semantic-commit-helper` prioritizing a language named in ARGUMENTS. This overrides `vault_name` (and the fallback to whichever vault is currently focused), and it applies even if `use_obsidian_cli` is `false`: naming a vault is itself a signal the user wants this note saved into Obsidian. The folder still comes from `artifacts.directory` as a vault-relative path (empty means vault root).

Keep the temp body file around until the session is finished with the note. To append `知見` later, edit that same local file and push the whole thing back:

```bash
python3 <skill-dir>/scripts/obsidian_stock.py overwrite \
  --path "<vault-relative path printed by create>" \
  --body /tmp/session-stock-body.md
```

If the script fails — Obsidian not running, CLI not installed, `vault_name` not among the known vaults, or no vault could be detected as active — surface its error message and stop. Don't fall back to writing the file somewhere else: the user pointed the config at a vault on purpose, and a note stashed in an unexpected directory is worse than no note.

## Execution steps

1. Check whether the slash-command ARGUMENTS that invoked this skill literally contain `plain=true`. If so, this run is in [plain mode](#plain-mode). Separately, check whether they literally contain `simplify=true`. If so, this run is in [simplify mode](#simplify-mode); otherwise simplify is off (default).
2. Review the current conversation and reconstruct the content section:
   - Not in plain mode: the transcript (`会話内容`).
   - In plain mode: every assistant utterance, in order, with user turns left out (`回答内容`).
   - Not in simplify mode (default): write that content verbatim, turn-by-turn.
   - In simplify mode: write that content as a condensed summary instead of a verbatim transcript.
   Generate the session summary either way.
3. Read `~/.config/session-stocker/config.toml` and resolve `artifacts.directory` and `use_obsidian_cli`. Determine the current local date and time (`YYYYMMDD_HHMM`) for the filename.
5. Check whether the user's request or slash-command ARGUMENTS name an Obsidian vault to save into. Save the note:
   - A vault was named explicitly: write the body to a temp file and run `scripts/obsidian_stock.py create --vault "<name>"` as described above, regardless of `use_obsidian_cli`.
   - No vault named, `use_obsidian_cli = false`: ensure the artifacts directory exists (create it if necessary) and write the file there using the required naming rule.
   - No vault named, `use_obsidian_cli = true`: write the body to a temp file and run `scripts/obsidian_stock.py create` as described above — it handles the naming rule and the directory itself.
6. Tell the user the saved path and briefly summarize what was captured.
7. Ask the user whether they want to add a `知見` section, e.g. 「知見を追加しますか？」. If they say yes, extract the durable learnings and add the `知見` section to the already-saved note (right after `会話内容` or `回答内容`, before `参考情報` if present) — editing the file directly, or via `scripts/obsidian_stock.py overwrite` when the Obsidian CLI is in use. If they decline or don't respond, leave the note as is.

## Quality bar

Before saving, check that:
- the file is actually written to disk (with `use_obsidian_cli = true`, the script's own round-trip check covers this — if it reports a mismatch, tell the user instead of retrying blindly)
- the filename matches the required pattern
- exactly one of `会話内容` (normal mode) or `回答内容` (plain mode) is present, matching whether `plain=true` was in the invoking ARGUMENTS — never both
- the `会話内容` section is a verbatim transcript of the actual exchange, not a summary or paraphrase — unless `simplify=true` was in the invoking ARGUMENTS, in which case it's a condensed summary instead
- the `回答内容` section, when present, contains only assistant utterances (no user turns), verbatim — unless `simplify=true` was in the invoking ARGUMENTS, in which case it's a condensed summary instead
- tool-call noise, raw command output, and system-reminder content are excluded from `会話内容` / `回答内容`
- the `知見` section is only present if the user explicitly asked for it, and if so, contains real takeaways rather than a repeat of the transcript
- the `参考情報` section appears only when relevant URLs exist
- when `参考情報` is present, it contains URLs only
- any link to another note in the stock directory follows the Obsidian-detection rule (wiki link vs. Markdown link), not a mix of both

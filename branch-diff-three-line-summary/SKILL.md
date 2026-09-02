---
name: branch-diff-three-line-summary
description: Summarize the committed changes of a Git branch (current branch by default, or a branch / PR number given as an argument) against the default branch in exactly three concise bullet points. Line length and writing style are adjustable via ~/.config/branch-diff-three-line-summary/config.toml. Use when the user wants a very short explanation of "this branch", "branch diff", or "changes on this branch". Not for commit messages, PR descriptions, code quality review, or uncommitted-only changes.
disable-model-invocation: true
---

# Branch Diff Three-Line Summary

Produce a compact explanation of what a Git branch changes, based on the committed diff from the default branch.

## Arguments

`$ARGUMENTS` may be empty, a branch name, or a PR number.

- Empty: summarize the current branch.
- Branch name: summarize that branch. Use `origin/<name>` if the local branch does not exist.
- PR number (digits only): resolve the head with
  ```bash
  gh pr view <n> --json headRefName,headRepositoryOwner,isCrossRepository
  ```
  For a same-repo PR, fetch and use the head branch:
  ```bash
  git fetch --quiet origin <headRefName>
  ```
  and take `<target>` as `origin/<headRefName>`. For a cross-repository (fork) PR, `origin/<headRefName>` does not exist, so fetch it into a local ref instead:
  ```bash
  git fetch --quiet origin pull/<n>/head:refs/branch-diff-summary/pr-<n>
  ```
  and take `<target>` as `refs/branch-diff-summary/pr-<n>`. If `gh` is unavailable or either command fails, say so in one line and stop.

Below, `<target>` means the resolved ref (`HEAD` when no argument is given), and `<base>` means the comparison base resolved in step 4 of the workflow.

## Configuration

The config file always lives at `~/.config/branch-diff-three-line-summary/config.toml`, regardless of where this skill itself is installed:

```toml
[output]
max_line_length = 100
style = "日本語の場合は常体 (だ・である調) を使う。"
```

- `max_line_length`: maximum characters per bullet body, excluding the leading `- `. Count full-width and half-width characters as one each.
- `style`: an extra free-text instruction about writing style. An empty string means no extra instruction.

The values shown above are the built-in defaults. If the file does not exist, use those defaults and continue. Do not create the file and do not mention that it is missing; the output must stay three bullets. `config.toml.template` in this skill's directory exists only as a starting point for users who want to override the defaults by hand.

Do not rely on a TOML parser. Read the file with `cat` and pick up `max_line_length = <integer>` and `style = "<string>"` under `[output]`. Apply these fallbacks silently:

- Missing key, or a `max_line_length` that is not a positive integer: use the built-in default shown above.
- `style = ""` set explicitly: no extra style instruction. This differs from a missing `style`, which falls back to the default 常体 instruction.

## Workflow

1. Load the configuration as described above.

2. Confirm you are in a Git repository:
   ```bash
   git rev-parse --show-toplevel
   ```

3. Identify the default branch:
   ```bash
   git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##'
   ```
   If `origin/HEAD` is unavailable, fall back to `main` if it exists, then `master` if it exists.

4. Refresh the comparison base so the summary is not made against a stale default branch, then resolve `<base>`:
   ```bash
   git fetch --quiet origin <default-branch> 2>/dev/null || true
   git rev-parse --verify --quiet origin/<default-branch>
   ```
   `<base>` is `origin/<default-branch>` when that ref resolves, otherwise the local `<default-branch>`. Use `<base>` in every command below; never assume the `origin/` prefix, because a repository without an `origin` remote only has the local branch.

5. Detached `HEAD` needs no special handling: treat `HEAD` as the target as usual.

6. Get the scope first. The `...` form already compares from the merge base, so no separate `merge-base` call is needed:
   ```bash
   git --no-pager diff --stat <base>...<target>
   git --no-pager diff --name-status <base>...<target>
   ```
   If `--stat` reports no changes, the branch has nothing of its own relative to `<base>` — this covers `<target>` being the default branch as well as an up-to-date branch. Return exactly three bullets saying there are no branch-specific changes and naming `<base>`. Judge this from the emptiness of the diff, not from the branch name: a local default branch that is ahead of `<base>` does have a real diff and must be summarized normally.

7. Read the patch with a size guard:
   - If the total changed lines in `--stat` are 800 or fewer, read the full patch:
     ```bash
     git --no-pager diff <base>...<target>
     ```
   - Otherwise, do not dump the full patch. Exclude generated and vendored files (`*.lock`, `package-lock.json`, `composer.lock`, `dist/`, `build/`, `vendor/`, `node_modules/`, minified assets, snapshot files), then read the remaining files one at a time with `git --no-pager diff <base>...<target> -- <path>`, starting from the files with the most changed lines, until the intent of the branch is clear. Use `git log --oneline <base>..<target>` as an additional hint for intent.

8. Base the summary on the actual diff, not only file names. Understand behavior, not just which files moved.

9. Only committed changes are in scope. Ignore staged and unstaged working tree changes, and do not mention them.

## Output rules

- Output exactly three bullet points, no heading and no extra prose.
- Give each bullet a fixed role:
  1. What changed: the main functional or structural change of the branch.
  2. How or why: the approach taken, or the reason it was needed, as far as the diff shows it.
  3. Impact: affected scope, behavioral risk, or what to check before merging or applying.
- Match the user's language. If the user asks in Japanese, answer in Japanese.
- Apply the `style` instruction from the configuration. With the default, Japanese output uses plain form (常体), not polite form.
- Keep each bullet body within `max_line_length` characters. If a bullet runs over, cut detail until it fits rather than wrapping.
- Prefer explaining user-visible or operational impact over listing filenames.
- Include filenames only when they clarify the change.
- Do not include commands, raw diff snippets, commit hashes, or speculation beyond what the diff supports.
- Do not write a commit message or PR body unless the user explicitly asks for that instead.

## Good output shape

```markdown
- 新リージョン向けの Terraform 設定を追加し、既存リージョンとの差分を最小限に抑えている。
- IAM と provider 設定を新リージョン向けに調整し、環境固有の値を変数へ分離した。
- 既存環境には影響しない追加変更だが、適用前に新リージョン向けの plan 確認が必要である。
```

## What to avoid

```markdown
- Changed 12 files.
- Updated infra/env/example/main.tf.
- Looks good.
```

This is too file-list oriented and does not explain the intent or impact of the branch.

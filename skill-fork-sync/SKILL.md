---
name: skill-fork-sync
description: >-
  Bring upstream changes into a skill you forked and then customized, one hunk at a time,
  without losing your own edits. Resolves the upstream repository and the local fork, shows
  every change between two upstream versions alongside the regions you customized, lets you
  pick what to take, and applies it. Use when the user says an upstream or original skill has
  a new version and they want that update merged into their fork, when they ask what changed
  upstream since the version their copy is based on, or when they name a skill repository and
  two versions and ask to pull the diff in. Trigger for phrasings like "fork した skill に本家の
  更新を取り込んで", "sync my fork with upstream v1.2.0 to v1.4.0", or "本家で何が変わったか見て
  取り込むものを選ばせて". Not for installing a skill for the first time, authoring a new skill
  from scratch, reviewing code, or summarizing release notes.
disable-model-invocation: true
argument-hint: "<owner/repo[/path] | github-url> <old-version> <new-version>"
allowed-tools: Read, Edit, Write, Glob, Grep, AskUserQuestion, Bash(git:*), Bash(gh:*), Bash(mkdir:*), Bash(cp:*), Bash(rm:*), Bash(ls:*), Bash(wc:*), Bash(head:*), Bash(cat:*), Bash(tar:*), Bash(diff:*), Bash(test:*), Bash(find:*)
---
# Skill Fork Sync

Merge upstream changes into a skill that was forked and then customized locally.

Fetching the diff is the easy part. The work is deciding, change by change, whether an upstream edit still makes sense on top of edits the user made for their own reasons. A fork exists because someone disagreed with something upstream, so nothing here merges silently: the upstream change and the local customization are put side by side, and the user decides.

## Arguments

`$ARGUMENTS` is `<upstream> <old-version> <new-version>`. All three are required.

`<upstream>` says where the original lives. Accepted forms:

- `owner/repo`
- `owner/repo/path/to/skill`
- `https://github.com/owner/repo`
- `https://github.com/owner/repo/tree/<ref>/<path>`

If no path is given and the repository holds more than one skill directory, list the candidates and ask which one.

`<old-version>` is the upstream version the fork is based on. `<new-version>` is the version to move to. Either may be a tag, a branch, or a commit SHA.

If a version does not resolve, retry once with the `v` prefix toggled (`1.3.0` to `v1.3.0`, or the reverse). If it still fails, print the ten most recent tags and stop.

Stop and say so when the two versions resolve to the same commit, or when `<old>` is not an ancestor of `<new>`. A reversed range hands the user their own history back as upstream news, which is worse than an error message.

## Workflow

### 1. Fetch the upstream history

Cache the clone at `~/.cache/skill-fork-sync/<owner>-<repo>/` so repeated syncs against the same upstream stay cheap.

```bash
git clone --filter=blob:none --no-checkout https://github.com/<owner>/<repo>.git <cache>
# when the cache already exists
git -C <cache> fetch --tags --quiet --prune
```

`--filter=blob:none --no-checkout` fetches file contents only when something asks for them, which keeps this under a second even for a large skills monorepo. Tags come with the clone, so `<old>` and `<new>` resolve without extra work.

If the clone fails (no network, private repository, no `gh` credentials), fall back to `gh api repos/<owner>/<repo>/compare/<old>...<new>` plus tarball downloads, and write the fallback into the report. A fallback that goes unreported reads exactly like a clean run.

### 2. Establish the range

```bash
git -C <cache> log --oneline <old>..<new> -- <path>
git -C <cache> diff --stat <old>..<new> -- <path>
```

If nothing under `<path>` changed between the two versions, say so and stop. There is no point resolving a fork for an empty range.

Keep the commit subjects. They are the best available statement of why each change was made, and step 8 needs them.

### 3. Find the fork

Look for the local copy in these places, in order:

- `<cwd>/.claude/skills/*/SKILL.md`
- `~/.claude/skills/*/SKILL.md`
- any `*/SKILL.md` in the current git work tree, when the current directory is one

Rank the candidates: first a `metadata.github-repo` in the frontmatter that matches the upstream repository, then a directory name or frontmatter `name` that matches the upstream skill.

Confirm with the user even when exactly one candidate matches. Patching the wrong skill is silent and tedious to undo.

When a directory cannot be read at all (a dangling symlink, a path the harness cannot cross), collect it and report it under `Skipped`. A fork that could not be seen looks identical to a fork that does not exist, and only the user can tell the two apart.

### 4. Note where the fork lives

```bash
git -C <fork-dir> rev-parse --show-toplevel
```

Inside a work tree, also run `git -C <fork-dir> status --short -- .`. Pre-existing uncommitted changes are worth mentioning before adding more on top.

Outside a work tree the fork is an installed copy: apply file by file, say so in the report, and remember there is no commit step and no easy undo.

### 5. Check the base

If the fork carries `metadata.github-ref` in its frontmatter, compare it with `<old>`. On a mismatch, name both versions and ask whether to continue.

This is the one error that quietly corrupts everything downstream. With the wrong base, edits the user made themselves get reported as upstream changes, and upstream changes they already took get offered a second time.

### 6. Lay out three trees

In a scratch directory, materialize:

- `base/` — upstream at `<old>`
- `theirs/` — upstream at `<new>`
- `ours/` — a copy of the fork

```bash
git -C <cache> archive <old> <path> | tar -x -C <scratch>/base --strip-components=<n>
git -C <cache> archive <new> <path> | tar -x -C <scratch>/theirs --strip-components=<n>
cp -r <fork-dir>/. <scratch>/ours/
```

`<n>` is the number of path components in `<path>`. Without it the two upstream trees keep the repository prefix while `ours` does not, and every later comparison has to special-case the difference.

`git archive` pulls the blobs it needs on demand, so it works against the partial clone.

### 7. Sort the files

| Situation | What to do |
| --- | --- |
| Added upstream | Offer to add it |
| Deleted upstream | Ask. The fork may reference it |
| Changed upstream, `ours` identical to `theirs` | Already taken. Say so, offer nothing |
| Changed upstream, `ours` identical to `base` | Clean take |
| Changed on both sides | Go to hunk level, step 8 |
| Present only in `ours` | A file the user added. List it, leave it alone |

Check `ours` against `theirs` before checking it against `base`. A fork that has already pulled part of this range differs from `base` everywhere it caught up, and diffing against `base` alone reports all of that as local customization. On a real fork sitting one version ahead of the `<old>` it was given, that mistake turns a two-hunk review into a nine-hundred-line one, all of it already present.

When listing files that exist only in `ours`, ignore generated and tooling paths: `.git/`, `__pycache__/`, `*.pyc`, `node_modules/`, `.DS_Store`. They are not customizations and reporting them buries the ones that are.

### 8. Describe each hunk

Split the file diff into one patch per hunk, so each can be probed and applied on its own:

```bash
git -C <cache> diff <old>..<new> -- <path>/<file> > <patch>
awk -v out=<scratch>/hunk '/^diff --git/{hdr=""} /^(diff --git|index |--- |\+\+\+ )/{hdr=hdr$0 ORS; next} /^@@/{n++; f=out n ".patch"; printf "%s", hdr > f} n{print > f}' <patch>
```

Then drop the hunks the fork already has:

```bash
cd <scratch>/ours && git apply --recount -p<n+1> --reverse --check <hunk>.patch 2>/dev/null
```

Success means that hunk is already present, so it should not be offered at all. Send the probe output to `/dev/null`: a failing `--check` is the normal answer to this question, and letting `git apply` print `patch does not apply` makes a successful classification look like a broken command.

For each hunk that remains, report three things:

- what it changes, in plain words rather than as raw patch text
- which commit introduced it, and that commit subject
- whether its line range overlaps a region the user changed, found by diffing `ours` against `base`

Overlap is the signal that matters. A hunk landing on untouched lines is mechanical. A hunk landing where the user deliberately rewrote something needs a judgment about intent, and that judgment is theirs.

Size guard: when the range changes more than roughly 800 lines under `<path>`, do not read the whole diff at once. Work file by file, `SKILL.md` first, then `references/`, then `scripts/`, and stop reading once the shape of the change is clear.

### 9. Let the user choose

Group the hunks by file. When there are many, offer "take every hunk that does not overlap your changes" as the first option. Most upstream releases are mostly mechanical, and making someone click through twenty trivial hunks to reach the two that matter spends their attention in the wrong place.

### 10. Apply

Pick the route by what the user selected:

- **Every hunk in a file, where `ours` diverges from `base`** — three-way merge the file:
  ```bash
  git merge-file --diff3 -L ours -L base -L upstream <ours>/<file> <base>/<file> <theirs>/<file>
  ```
  Exit code 0 means a clean merge. A positive exit code is the number of conflicts, left marked in place; resolve every marker by hand before the file is saved.
- **A subset of hunks** — apply the per-hunk patches from step 8, one at a time:
  ```bash
  cd <scratch>/ours && git apply --recount -p<n+1> --check <hunk>.patch   # then again without --check
  ```
  `git apply` works outside a git repository, so this route covers installed copies as well as work trees.
- **Anything that fails to apply** — read the upstream intent and the local version, then edit by hand so both survive. In a customized fork the context lines around a hunk are routinely different, so mechanical application failing is the normal case, not an exception worth apologizing for.

Never apply a hunk to `metadata.github-*`. Those lines are written by the installer, not by upstream.

Record which route each hunk took. "Applied" and "applied after rewriting it to fit your version" are different facts, and the user needs both to know what to re-read.

### 11. Update the recorded base

Only when every upstream change was taken, set the fork frontmatter `github-ref` to `<new>` and `github-tree-sha` to:

```bash
git -C <cache> rev-parse <new>:<path>
```

On a partial take, leave both at `<old>` and say so. A tree SHA claiming a version that was never fully taken makes the next sync start from a base that never existed, which is the failure step 5 exists to catch.

### 12. Offer to commit

Only when the fork is inside a git work tree, and only by asking. Stage the skill directory alone, and put the upstream range in the message:

```
chore(<skill>): sync upstream <old>..<new>
```

Ask again, separately, before pushing or opening a pull request.

## Output rules

Report under these headings, in this order:

```markdown
## Upstream range
<owner/repo/path> <old> -> <new> (N commits, +X/-Y lines)

## Your fork
<path> (git work tree: yes/no, base recorded as: <ref>)

## Changes
| File | Hunk | What it changes | Overlaps your customization |

## Applied
| Hunk | How |

## Left as is
Hunks declined, hunks already present in the fork, and local-only files left untouched.

## Skipped
Directories that could not be read, and any fallback taken.
```

- Describe hunks by behavior, not by patch text. Show the raw diff only when asked, or when the change is a wording edit where the exact text is the point.
- State every fallback explicitly: a cache clone that failed over to the API, an unreadable directory, a hunk that needed hand-merging. Silence here reads as success.
- Never report a hunk as applied without having applied it.
- Match the language the user writes in. If they ask in Japanese, answer in Japanese.

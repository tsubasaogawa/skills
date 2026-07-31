---
name: pr-branch-composition-check
description: "Verify that a GitHub pull request is composed ONLY of commits from a specific set of branches/PRs, and flag any commit that came from somewhere else. Use this skill whenever the user asks to confirm a PR is built purely from named parent branches or PRs, wants to check for stray/leaked commits mixed into a stacked PR, or says things like 'このPRが指定したブランチだけで構成されているか確認して', 'PRに他のブランチのコミットが混ざっていないかチェックして', '◯◯と◯◯と◯◯のブランチだけで構成されていることを証明して', or 'make sure this PR only contains commits from #1234 and #5678'. This is a commit-provenance audit, not a general code review — do NOT use it for reviewing code quality, correctness, or diff content (use a review skill for that instead)."
allowed-tools: "Bash(gh:*), Bash(git:*)"
metadata:
  version: 0.0.1
---

# PR Branch Composition Check

Mechanically verify that a target PR is composed only of commits from a specified set of branches (given as branch names or PR numbers). The goal is not review — it's provenance proof. Cross-reference the target PR's commit list against the specified branches' commit lists, and for any leftover commits, identify what they actually are and classify them as expected or anomalous.

## 1. Identify the target and the specified branches

Pin down two things first.

- **Target PR**: usually given by number. If the user says "this PR", resolve it from the immediate conversation context.
- **Specified branches**: there are two sources, and explicit user input always takes priority.
  1. **The user names them directly in conversation** (e.g. "check that this is composed only of branches A, B, and C") — use those branch names/PR numbers as given.
  2. **The user defers to the PR description** (e.g. "the ones listed in the PR body") — read the parent branches/PRs from the target PR's body. Look for enumerations like `#1234` following phrasing such as "Parent branches:", "Stacked on", or "Depends on". Handle formatting variance too (bare numbers, full URLs, raw branch names).

If both are present and they disagree, ask the user to confirm which one to use.

```bash
gh pr view <PR_NUMBER> --json body,commits,baseRefName,headRefName
```

## 2. Fetch the commit list for the target PR and each specified branch

Target PR's commit SHAs:

```bash
gh pr view <PR_NUMBER> --json commits -q '.commits[].oid'
```

How you fetch the specified branches' commits depends on whether each was given as a PR number or a branch name.

- If given as a PR number:

  ```bash
  gh pr view <PARENT_PR_NUMBER> --json commits -q '.commits[].oid'
  ```

- If given as a branch name (local or remote), take every commit reachable from the branch tip since it diverged from its base (usually `master` or `main`):

  ```bash
  git log <base>..<branch> --format=%H
  ```

  If the base is unclear, pin down the divergence point with `git merge-base <base> <branch>` first, then fetch commits the same way.

## 3. Extract the difference

Subtract the specified branches' commit SHAs (union across all of them) from the target PR's full commit SHA list. What's left is "commits that exist only in the target PR." If nothing is left, you can already conclude that no commits from outside the specified branches are present.

## 4. Identify what the leftover commits actually are, and classify them

For each leftover commit, start by checking its parent count and subject line.

```bash
git show -s --format='%H %s%n%an %ad%n%P' <commit-sha>
```

### 4-1. Classifying regular merge workflows

- **Expected (merge commit)**: the commit has two or more parents, and the merge source is one of the specified branches — typically a subject line like `Merge pull request #<PR_NUMBER_FROM_SPECIFIED_BRANCHES> from ...`. This naturally occurs in a stacked workflow where the specified branches are merged into `master` one after another (merge one branch's PR, then branch the next one off the updated `master`, repeat). The merge commit itself introduces no new content, so treat it as an **expected** diff, not an anomaly.
- **Undetermined**: if the commit has only one parent, don't immediately call it anomalous. A squash-merged PR can produce a commit that's indistinguishable from a regular commit at this stage, so move on to 4-2 to inspect its actual content before deciding.

### 4-2. Handling squash-merge workflows (where the SHA gets rewritten)

GitHub's squash-merge collapses every commit in a PR into a single commit with one parent, landed on `master`. Because the SHA is rewritten, neither the SHA cross-reference in step 3 nor the "two or more parents" check in 4-1 can catch this case. The fix is to shift the basis of comparison from **SHA equality** to **diff-content equality**.

1. **Check the PR number in the subject line first.** GitHub's default squash-merge commit message format is `<PR title> (#<PR_NUMBER>)`. If the `(#xxxx)` at the end of the subject line matches one of the specified branches' PR numbers, that's a strong signal on its own.

   ```bash
   git show -s --format='%s' <commit-sha>
   ```

2. **Cross-check the diff content with `git patch-id`.** When the subject line alone isn't conclusive (e.g. the branch was specified by name and there's no PR number to check, or you just want independent confirmation), use `git patch-id`. It hashes only the diff content, ignoring commit metadata (SHA, timestamp, author) — so the same change produces the same hash even after the SHA has been rewritten.

   For the suspect commit (single parent, so `<sha>^` is its parent):

   ```bash
   git diff <commit-sha>^..<commit-sha> | git patch-id --stable
   ```

   For the cumulative diff of the specified branch. If it was given as a PR number, `gh pr diff` conveniently outputs the PR's full cumulative diff:

   ```bash
   gh pr diff <PARENT_PR_NUMBER> | git patch-id --stable
   ```

   If given as a branch name:

   ```bash
   git diff "$(git merge-base <base> <branch>)".."<branch>" | git patch-id --stable
   ```

   If the hash (first field of the output) matches on both sides, the commit is the squash-merge result of that specified branch — classify it as **expected**.

3. **If the hashes don't match**, extra changes may have been folded in after the squash (e.g. addressing review comments post-merge). Compare `git diff <commit-sha>^..<commit-sha> --stat` against the specified branch's diff file-by-file; if there are changes not present on the specified branch's side, classify it as **anomalous**.

### Classification summary

- **Expected (merge commit)**: two or more parents, merge source is one of the specified branches
- **Expected (squash-merge)**: single parent, but confirmed as coming from a specified branch via a matching PR number in the subject line or a matching `git patch-id`
- **Anomalous (contamination)**: none of the above apply — a regular code commit, a merge commit unrelated to the specified branches, or a patch-id mismatch where the file diff also contains changes absent from any specified branch

**Remaining limitation**: `git patch-id` assumes the diff content is an exact match. If even a single line differs after the squash — say, from resolving a merge conflict — the hashes won't match, and automatic classification stops there. In that case, fall back to a manual file-by-file review with `git diff --stat` / `git diff`. That said, "the SHA gets rewritten, so there's no way to verify it" no longer holds — diff-content equality can still be checked mechanically before you ever need to fall back to manual review.

## 5. Report the result

Report using this structure.

1. **Commit breakdown**: show, as a table or bullet list, which specified branch (PR) each of the target PR's commits came from
2. **Handling of leftover commits** (only if any exist): for each leftover commit, state what it actually is (merge commit or not, source PR) and whether it's classified as expected or anomalous
3. **Conclusion**: end with one definitive sentence, e.g. "No commits from outside the specified branches are present" or "Commit XYZ was contaminated from outside the specified branches"

It's fine to lead with the conclusion before the breakdown table, so the reader gets the answer immediately. Avoid a long preamble.

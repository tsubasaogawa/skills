---
name: ai-credit-efficient-review
description: "Review a pull request, branch diff, or changed files while using AI Credit efficiently. Use this skill whenever the user asks for a cheaper review, a lightweight review, a high-signal review, a review that prioritizes only major issues, or mentions AI Credit / cost efficiency in the context of code review. Trigger for prompts like 'AI Credit を節約しつつレビューして', '軽めにレビューして', '重大な問題だけ見て', or 'review this PR efficiently'. Prefer this skill over an exhaustive review when the user wants cost-awareness. Do not use it when the runtime has already forced a dedicated /review workflow, or when the user explicitly asks for a full exhaustive review regardless of cost."
allowed-tools: "Read, Glob, Bash(git:*), Bash(gh:*), Bash(python:*), Bash(ls:*)"
metadata:
  version: 0.0.2
---

# AI Credit Efficient Review

Perform a **high-signal, cost-aware review**. The goal is not to read everything equally. The goal is to spend the cheapest effort that still gives the user useful risk detection.

## Core idea

Default to a two-stage review:

1. **Cheap triage first** to understand scope, size, and risk.
2. **Selective deepening** only on the files or behaviors that deserve more attention.

This usually saves AI Credit because the expensive part of review is broad, repeated reasoning over low-risk changes. A fast scope pass lets you avoid that.

## When to keep the review lightweight

Stay in lightweight mode when most of these are true:

- the diff is small
- changed files are few and localized
- changes are documentation, comments, naming, or straightforward wiring
- no security, permissions, auth, data, CI/CD, production Terraform, or migration hotspots appear
- the user asked for "major issues only", "quick review", or "AI Credit efficient review"

In lightweight mode, do **not** invoke a heavy review subagent. Use direct commands and direct file inspection.

## When to deepen or escalate

Deepen the review when cheap triage shows real risk, for example:

- authentication, authorization, IAM, secrets, encryption, network policy
- Terraform for production or shared/global infrastructure
- schema changes, migrations, destructive operations, data handling
- GitHub Actions, deployment logic, rollback-sensitive automation
- large diffs, cross-cutting refactors, or many files with coupled behavior
- the user explicitly asks for a deeper or more exhaustive review

If escalation is needed, do it **once** and with a narrowed scope. Pass the risky files, risk reasons, and review goal instead of asking a subagent to rediscover the whole repository.

## Workflow

### 1. Identify the review target

Determine whether the user wants to review:

- a GitHub PR number
- the current branch diff
- specific changed files

If the target is obvious from the request, proceed. Ask only if you truly cannot tell what should be reviewed.

### 2. Run cheap scope triage first

Always start with the bundled script. `<skill-dir>` below means this skill's base directory (announced when the skill is invoked); do not assume any particular install location.

```bash
python <skill-dir>/scripts/review_scope.py --pr <PR_NUMBER>
```

or for the current branch:

```bash
python <skill-dir>/scripts/review_scope.py --current-branch
```

If needed, compare explicit refs:

```bash
python <skill-dir>/scripts/review_scope.py --base <BASE_REF> --head <HEAD_REF>
```

The script prints JSON with everything triage needs:

- `files`: per-file insertions/deletions plus hotspot labels, so you can rank what to read
- `hotspots`: risky categories (auth/IAM, terraform, migrations, CI, production scope) with the matching files
- `skippable_files`: lockfiles, generated artifacts, vendored code, binary assets — do not read their diffs; at most confirm they are what they look like from the path
- `substantive_file_count` / `substantive_changed_lines`: size of the change **excluding** skippable noise; use these, not the raw totals, to judge how big the review really is
- `largest_files`: the biggest substantive files, a good default reading order after hotspots
- `recommended_review_mode` and `risk_reasons`: the script's lightweight/escalate suggestion

### 3. Read only what matters first

Before reading patches, prioritize files in this order:

1. hotspot files flagged by the triage script
2. config or infra entrypoints that fan out behavior
3. the `largest_files` entries, since big diffs hide more bugs
4. tests covering risky code
5. only then the remaining changed files if still necessary

Never spend reading time on `skippable_files`. A 3000-line lockfile diff is not a 3000-line review.

Do not read the same diff repeatedly through multiple tools unless new information justifies it.

## Review strategy by mode

### Lightweight mode

Use direct `git` or `gh` commands plus targeted file reads.

Recommended commands:

```bash
git --no-pager diff --stat <range>
git --no-pager diff --name-status <range>
git --no-pager diff <range> -- <important-paths>
```

For PRs, you can also use:

```bash
gh pr diff <PR_NUMBER> --name-only
gh pr view <PR_NUMBER> --json title,body,files
```

Keep the investigation narrow. Focus on correctness risks, not line-by-line commentary.

### Escalated mode

If the change is genuinely risky, call a code-review style subagent **once** with:

- the exact review target
- the hotspot file list
- the risk reasons from triage
- a request to focus on substantive issues only

Do not launch both exploratory and review agents over the same scope. Do not rerun equivalent reviews unless the user changes the goal or new evidence appears.

## Output format

Lead with the result.

When there are findings, return:

1. a short verdict
2. only the meaningful findings, prioritized by severity
3. file references when available

When there are no findings, say that plainly.

Keep the response concise. The whole point of this skill is to save both AI Credit and the user's time.

## What to avoid

- exhaustive commentary on every touched file
- style-only feedback unless the user asked for it
- repeatedly re-summarizing the whole diff
- launching a heavy review agent before cheap triage
- using multiple heavy agents for the same review target
- pretending the review was exhaustive when it was intentionally selective

## Example behavior

### Example 1: cheap PR review

**User**

```text
PR #1234 を AI Credit を節約しつつレビューして。重大な問題だけ見たい。
```

**Good behavior**

1. Run triage for PR #2575.
2. If the diff is small and localized, inspect only the changed files directly.
3. Return either "no substantive issues" or a short list of real risks.

### Example 2: escalate because risk is high

**User**

```text
この PR は IAM と production Terraform を触っています。AI Credit は意識しつつも見落としは減らしたいです。
```

**Good behavior**

1. Run triage.
2. Notice the security / shared-infra hotspots.
3. Narrow the scope to those files and escalate once if direct inspection is not enough.

## Why this works

Cost-aware review is mostly about **better selection**, not weaker thinking. Triage cheaply, spend depth where the risk is concentrated, and avoid paying for broad reasoning that adds little value.

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path


HOTSPOT_RULES = [
    (re.compile(r"(^|/)\.github/workflows/"), "github-actions"),
    (re.compile(r"(^|/)(iam|identity|auth|oauth|sso)(/|$)", re.IGNORECASE), "auth-or-iam"),
    (re.compile(r"(^|/)(terraform|tfvars|terragrunt)(/|$)|\.tf(vars)?$|terragrunt\.hcl$", re.IGNORECASE), "terraform"),
    (re.compile(r"(^|/)(migrations?|schema|ddl|sql)(/|$)|\.sql$", re.IGNORECASE), "database-change"),
    (re.compile(r"(^|/)(prod|production|global|shared)(/|$)", re.IGNORECASE), "shared-or-production-scope"),
    (re.compile(r"(^|/)(secrets?|kms|policy|security)(/|$)", re.IGNORECASE), "security-sensitive"),
    (re.compile(r"(^|/)(scripts?|deploy|release|pipeline)(/|$)", re.IGNORECASE), "automation"),
]

LOW_VALUE_RULES = [
    (
        re.compile(
            r"(^|/)(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|poetry\.lock|uv\.lock|Cargo\.lock|composer\.lock|Gemfile\.lock|go\.sum)$"
        ),
        "lockfile",
    ),
    (
        re.compile(r"(^|/)(dist|build|vendor|node_modules|__snapshots__|__generated__|generated)(/|$)", re.IGNORECASE),
        "generated-or-vendored",
    ),
    (re.compile(r"\.(min\.js|min\.css|map|snap)$"), "generated-artifact"),
    (re.compile(r"\.(png|jpe?g|gif|ico|woff2?|ttf|eot|pdf|zip|gz)$", re.IGNORECASE), "binary-asset"),
]


def run(cmd: list[str]) -> str:
    completed = subprocess.run(
        cmd,
        check=True,
        text=True,
        capture_output=True,
    )
    return completed.stdout


def try_run(cmd: list[str]) -> str | None:
    try:
        return run(cmd)
    except subprocess.CalledProcessError:
        return None


def ensure_repo() -> None:
    run(["git", "rev-parse", "--show-toplevel"])


def hotspot_labels(path: str) -> list[str]:
    return [label for pattern, label in HOTSPOT_RULES if pattern.search(path)]


def low_value_label(path: str) -> str | None:
    for pattern, label in LOW_VALUE_RULES:
        if pattern.search(path):
            return label
    return None


def build_file_entries(stats: list[tuple[str, int, int]]) -> list[dict[str, object]]:
    return [
        {
            "path": path,
            "insertions": insertions,
            "deletions": deletions,
            "hotspots": hotspot_labels(path),
            "low_value": low_value_label(path),
        }
        for path, insertions, deletions in stats
    ]


def parse_numstat(text: str) -> list[tuple[str, int, int]]:
    stats: list[tuple[str, int, int]] = []
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        ins, dele, path = parts[0], parts[1], parts[2]
        stats.append(
            (
                path,
                int(ins) if ins.isdigit() else 0,
                int(dele) if dele.isdigit() else 0,
            )
        )
    return stats


def extension_counts(paths: list[str]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for path in paths:
        suffix = Path(path).suffix.lower() or "<no-ext>"
        counter[suffix] += 1
    return dict(counter.most_common())


def grouped_hotspots(entries: list[dict[str, object]]) -> list[dict[str, object]]:
    hits: dict[str, set[str]] = {}
    for entry in entries:
        for label in entry["hotspots"]:
            hits.setdefault(label, set()).add(entry["path"])
    return [
        {"label": label, "files": sorted(files)}
        for label, files in sorted(hits.items())
    ]


def recommend_mode(
    substantive_file_count: int,
    hotspots: list[dict[str, object]],
    substantive_changed_lines: int,
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    hotspot_labels_present = {item["label"] for item in hotspots}

    if substantive_file_count >= 12:
        reasons.append("many changed files")
    if substantive_changed_lines >= 400:
        reasons.append("large line delta")
    if hotspot_labels_present & {
        "auth-or-iam",
        "terraform",
        "database-change",
        "security-sensitive",
        "shared-or-production-scope",
    }:
        reasons.append("high-risk file categories present")

    mode = "escalate" if reasons else "lightweight"
    return mode, reasons


def summarize(stats: list[tuple[str, int, int]]) -> dict[str, object]:
    entries = build_file_entries(stats)
    substantive = [e for e in entries if e["low_value"] is None]
    substantive_lines = sum(e["insertions"] + e["deletions"] for e in substantive)
    hotspots = grouped_hotspots(entries)
    review_mode, risk_reasons = recommend_mode(len(substantive), hotspots, substantive_lines)
    largest = sorted(substantive, key=lambda e: e["insertions"] + e["deletions"], reverse=True)
    return {
        "file_count": len(entries),
        "insertions": sum(e["insertions"] for e in entries),
        "deletions": sum(e["deletions"] for e in entries),
        "substantive_file_count": len(substantive),
        "substantive_changed_lines": substantive_lines,
        "files": entries,
        "extensions": extension_counts([e["path"] for e in entries]),
        "hotspots": hotspots,
        "skippable_files": [e["path"] for e in entries if e["low_value"] is not None],
        "largest_files": [e["path"] for e in largest[:5]],
        "recommended_review_mode": review_mode,
        "risk_reasons": risk_reasons,
    }


def summary_from_pr(pr_number: str) -> dict[str, object]:
    raw = run(
        [
            "gh",
            "pr",
            "view",
            pr_number,
            "--json",
            "number,title,baseRefName,headRefName,files",
        ]
    )
    pr = json.loads(raw)
    stats = [
        (item["path"], int(item.get("additions", 0)), int(item.get("deletions", 0)))
        for item in pr.get("files", [])
    ]
    result = summarize(stats)
    result.update(
        {
            "target_type": "pull_request",
            "target": f"PR #{pr['number']}",
            "title": pr.get("title"),
            "base_ref": pr.get("baseRefName"),
            "head_ref": pr.get("headRefName"),
        }
    )
    # gh pr view returns at most 100 files
    if len(stats) >= 100:
        result["warning"] = "file list may be truncated at 100 entries; verify with gh pr diff --name-only"
    return result


def resolve_default_branch() -> str:
    remote_head = try_run(
        ["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"]
    )
    if remote_head:
        return remote_head.strip().removeprefix("origin/")
    for candidate in ("main", "master"):
        if try_run(["git", "rev-parse", "--verify", candidate]):
            return candidate
    raise RuntimeError("Could not determine default branch")


def summary_from_range(base: str, head: str) -> dict[str, object]:
    numstat = run(["git", "--no-pager", "diff", "--numstat", f"{base}...{head}"])
    result = summarize(parse_numstat(numstat))
    result.update(
        {
            "target_type": "git_range",
            "base_ref": base,
            "head_ref": head,
        }
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Cheap triage for cost-aware code review")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pr", help="GitHub pull request number")
    group.add_argument("--current-branch", action="store_true", help="Compare current branch against default branch")
    group.add_argument("--base", help="Explicit base ref")
    parser.add_argument("--head", help="Explicit head ref; required with --base")
    args = parser.parse_args()

    ensure_repo()

    try:
        if args.pr:
            result = summary_from_pr(args.pr)
        elif args.current_branch:
            head = run(["git", "branch", "--show-current"]).strip()
            default_branch = resolve_default_branch()
            if head == default_branch:
                sys.stderr.write(
                    f"current branch is the default branch ({default_branch}); diff is empty by definition\n"
                )
            result = summary_from_range(default_branch, head)
            result["target"] = f"{head} vs {default_branch}"
        else:
            if not args.head:
                raise RuntimeError("--head is required when --base is used")
            result = summary_from_range(args.base, args.head)
            result["target"] = f"{args.head} vs {args.base}"
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(exc.stderr or str(exc))
        return exc.returncode
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"{exc}\n")
        return 1

    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

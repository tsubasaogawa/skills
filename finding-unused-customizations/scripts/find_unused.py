"""List custom Claude Code skills and subagents with their recent usage counts.

Usage:
    python find_unused.py [--days N] [--claude-home DIR] [--project-root DIR]
                          [--projects-dir DIR ...]

Definitions are read from <claude-home>/skills, <claude-home>/agents,
<project-root>/.claude/skills and <project-root>/.claude/agents.
Usage is counted from Claude Code transcripts (*.jsonl) under
<claude-home>/projects and each --projects-dir, using only records whose
timestamp falls inside the period:

- Skill tool calls (input.skill)
- Agent / Task tool calls (input.subagent_type)
- Slash commands typed by the user (<command-name>...</command-name>)

Prints one JSON document to stdout.
"""

import argparse
import datetime as dt
import glob
import json
import os
import re
import sys

COMMAND_RE = re.compile(r"<command-name>/?([^<\s]+)</command-name>")
KEY_RE = re.compile(r"^([A-Za-z0-9_-]+):\s*(.*)$")


def parse_frontmatter(text):
    """Return (fields, issues) for the simple YAML subset used in SKILL.md."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, ["no frontmatter"]
    issues = []
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        issues.append("frontmatter is not closed")
        end = len(lines)
    elif lines[end] != "---":
        issues.append("closing --- is indented (line %d)" % (end + 1))

    fields = {}
    key = None
    for line in lines[1:end]:
        m = KEY_RE.match(line)
        if m:
            key, value = m.group(1), m.group(2).strip()
            if value in (">", "|", ">-", "|-"):
                value = ""
            elif len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            fields[key] = value
        elif key and line.strip():
            fields[key] = (fields[key] + " " + line.strip()).strip()
    return fields, issues


def definition(kind, scope, name, md_path):
    d = {"kind": kind, "scope": scope, "name": name, "path": md_path,
         "description": None, "issues": []}
    try:
        with open(md_path, encoding="utf-8") as f:
            fields, issues = parse_frontmatter(f.read())
    except OSError as e:
        d["issues"].append("unreadable: %s" % e)
        return d
    d["description"] = fields.get("description")
    d["frontmatter_name"] = fields.get("name")
    d["issues"].extend(issues)
    if d["frontmatter_name"] and d["frontmatter_name"] != name:
        d["issues"].append("frontmatter name is %s" % d["frontmatter_name"])
    return d


def scan(claude_dir, scope):
    defs = []
    for path in sorted(glob.glob(os.path.join(claude_dir, "agents", "*.md"))):
        defs.append(definition("agent", scope, os.path.basename(path)[:-3], path))
    skills_dir = os.path.join(claude_dir, "skills")
    names = sorted(os.listdir(skills_dir)) if os.path.isdir(skills_dir) else []
    for name in names:
        path = os.path.join(skills_dir, name)
        if name.startswith(".") or os.path.isfile(path):
            continue
        # A broken or unreachable link is neither a file nor a dir; reading SKILL.md reports it.
        defs.append(definition("skill", scope, name, os.path.join(path, "SKILL.md")))
    return defs


def count_usage(projects_dirs, cutoff):
    usage = {"skill": {}, "agent": {}, "command": {}}
    cutoff_iso = cutoff.strftime("%Y-%m-%dT%H:%M:%S")
    files = 0
    seen = set()  # forked and resumed sessions repeat records; count each uuid once
    for pdir in projects_dirs:
        for path in glob.glob(os.path.join(pdir, "**", "*.jsonl"), recursive=True):
            if os.path.getmtime(path) < cutoff.timestamp():
                continue
            files += 1
            with open(path, encoding="utf-8", errors="replace") as f:
                for line in f:
                    try:
                        rec = json.loads(line)
                    except ValueError:
                        continue
                    uid = rec.get("uuid")
                    if (rec.get("timestamp") or "")[:19] < cutoff_iso or (uid and uid in seen):
                        continue
                    seen.add(uid)
                    content = (rec.get("message") or {}).get("content")
                    for name in invocations(rec.get("type"), content):
                        table = usage[name[0]]
                        table[name[1]] = table.get(name[1], 0) + 1
    return usage, files


def invocations(rec_type, content):
    if rec_type == "assistant" and isinstance(content, list):
        for part in content:
            if not isinstance(part, dict) or part.get("type") != "tool_use":
                continue
            inp = part.get("input") or {}
            if part.get("name") == "Skill" and inp.get("skill"):
                yield "skill", inp["skill"]
            elif part.get("name") in ("Agent", "Task") and inp.get("subagent_type"):
                yield "agent", inp["subagent_type"]
    elif rec_type == "user":
        texts = [content] if isinstance(content, str) else [
            p.get("text", "") for p in content or [] if isinstance(p, dict)]
        for text in texts:
            for m in COMMAND_RE.finditer(text):
                yield "command", m.group(1)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--claude-home", default=os.path.expanduser("~/.claude"))
    ap.add_argument("--project-root", default=os.getcwd())
    ap.add_argument("--projects-dir", action="append", default=[])
    args = ap.parse_args()

    # The period starts at local midnight, <days> days before today, so "14 days" covers whole days.
    now = dt.datetime.now(dt.timezone.utc)
    start = dt.datetime.combine(dt.date.today() - dt.timedelta(days=args.days), dt.time())
    cutoff = start.astimezone(dt.timezone.utc)
    defs = scan(args.claude_home, "user") + scan(os.path.join(args.project_root, ".claude"), "project")

    projects_dirs = [os.path.join(args.claude_home, "projects")] + args.projects_dir
    missing = [d for d in projects_dirs if not os.path.isdir(d)]
    usage, files = count_usage([d for d in projects_dirs if d not in missing], cutoff)

    matched = set()
    for d in defs:
        names = {d["name"], d.get("frontmatter_name")} - {None}
        sources = ("skill", "command") if d["kind"] == "skill" else ("agent",)
        d["uses"] = 0
        for src in sources:
            for n in names:
                if n in usage[src]:
                    d["uses"] += usage[src][n]
                    matched.add((src, n))

    unmatched = [{"source": src, "name": n, "count": c}
                 for src, table in usage.items() for n, c in sorted(table.items())
                 if (src, n) not in matched and ":" not in n]

    sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp932 etc.
    print(json.dumps({
        "period_utc": [cutoff.strftime("%Y-%m-%dT%H:%M:%S"), now.strftime("%Y-%m-%dT%H:%M:%S")],
        "projects_dirs": projects_dirs,
        "missing_projects_dirs": missing,
        "transcript_files": files,
        "definitions": defs,
        "unmatched_invocations": unmatched,
    }, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

"""Extract one day's user / assistant text from Claude Code transcripts.

Usage:
    python extract_today.py --out DIR [--date YYYY-MM-DD] [--projects-dir DIR] [--exclude SESSION_ID]

Writes one text file per session that has messages on --date (local time).
Messages already written for another session are skipped, because a fork
repeats its parent's history.
"""

import argparse
import datetime as dt
import glob
import json
import os


def local_date(ts):
    try:
        return dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone().date().isoformat()
    except ValueError:
        return None


def texts(record):
    content = (record.get("message") or {}).get("content")
    if isinstance(content, str):
        yield content
    elif isinstance(content, list):
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text" and part["text"].strip():
                yield part["text"]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--date", default=dt.date.today().isoformat())
    p.add_argument("--projects-dir", default=os.path.expanduser("~/.claude/projects"))
    p.add_argument("--exclude", default="")
    a = p.parse_args()

    os.makedirs(a.out, exist_ok=True)
    seen = set()
    files = sorted(glob.glob(os.path.join(a.projects_dir, "*", "*.jsonl")), key=os.path.getmtime)
    total = 0
    for f in files:
        sid = os.path.basename(f)[:-6]
        if a.exclude and sid.startswith(a.exclude):
            continue
        lines = []
        with open(f, encoding="utf-8") as fh:
            for raw in fh:
                try:
                    r = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                role = r.get("type")
                if role not in ("user", "assistant") or local_date(r.get("timestamp", "")) != a.date:
                    continue
                for t in texts(r):
                    if (role, t) in seen:
                        continue
                    seen.add((role, t))
                    lines.append(f"{role.upper()}: {t[:1500 if role == 'user' else 2500]}")
        if not lines:
            continue
        body = "\n\n".join(lines)
        with open(os.path.join(a.out, sid[:8] + ".txt"), "w", encoding="utf-8") as fh:
            fh.write(body)
        total += len(body)
        print(f"{sid[:8]}.txt\t{len(body)}\t{os.path.basename(os.path.dirname(f))}")
    print(f"total_chars={total}")


if __name__ == "__main__":
    main()

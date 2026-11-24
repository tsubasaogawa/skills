"""PreCompact hook: pass the instructions written by /preparing-compact to compact as its summarization instructions.

The instructions live at .claude/compact-instructions/<session_id>.md.
If the file exists, print it to stdout (Claude Code uses it as the summarization instructions) and delete it afterward.
Otherwise, print nothing and let compact proceed as usual.
"""

import json
import sys
from pathlib import Path

INSTRUCTIONS_DIR = Path(__file__).resolve().parents[3] / "compact-instructions"


def main() -> int:
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")

    session_id = json.load(sys.stdin).get("session_id")
    if not session_id:
        return 0

    path = INSTRUCTIONS_DIR / f"{session_id}.md"
    if not path.is_file():
        return 0

    sys.stdout.write(path.read_text(encoding="utf-8"))
    path.unlink()
    return 0


if __name__ == "__main__":
    sys.exit(main())

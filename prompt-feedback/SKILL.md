---
name: prompt-feedback-skill
description: Provide structured feedback on the user's messages in the conversation using the "good / more / next action" framework.
allowed-tools: Bash(mkdir:*), Bash(cat:*), Write
metadata:
  version: 0.0.1
---

# Instructions

Analyze all user messages in this conversation (user messages only; prioritize latest intent on conflict) and provide structured feedback focused on improving the prompt. Always respond in the **same language as the user**.

## Rules

- Internally synthesize all user messages into one consolidated instruction (do not output).
- Identify **good** (strengths), **more** (missing info), and **next action** (one concrete step).
- Unresolvable contradictions → list under **more**.
- **next action** must be exactly one concrete step (a question, metric, or command).
- No extra sections. Keep it concise and actionable.

## Output format

Respond, then save to `~/.local/share/prompt-feedback-skill/YYYYMMDD-HHMMSS.md` using the machine's local timezone (e.g., `date +%Y%m%d-%H%M%S` without `-u`; `mkdir -p` when the directory does not exist).

Saved file adds a `# <one-line summary>` header before the sections below.

```
## good
- ...

## more
- ...

## next action
- ...
```

---
name: drafting-tweet-from-today
description: List the insights gained from the day's Claude Code sessions, narrow them to 3 candidate themes for X (Twitter), let the user pick one, and draft a tweet of 140 characters or fewer. Use for requests like "turn today's insights into a tweet" or "give me something to post on X". Does not post.
disable-model-invocation: true
argument-hint: "[YYYY-MM-DD]"
allowed-tools: Read, AskUserQuestion, Agent, Bash(python -I:*)
metadata:
  version: 0.0.1
---

# Drafting Tweet From Today

Pick up insights from the day's sessions and write one draft tweet for X. The only deliverable is the draft shown in chat. Do not post, save to memory, or edit notes.

## 1. Extract the day's sessions

Use the bundled script to write only the user and assistant messages from the given date into one text file per session.

```bash
python -I ~/.claude/skills/drafting-tweet-from-today/scripts/extract_today.py --out <scratchpad>/tx --exclude <first 8 chars of the current session ID>
```

- If a date is given as an argument, pass it as `--date YYYY-MM-DD`. Defaults to today (local time)
- Exclude the current session with `--exclude`. Its ID is the file name of the newest jsonl in `~/.claude/projects/<project>/`
- Forked sessions repeat their parent's history, so the script skips messages it has already written. A fork's file contains only the diff
- Old sessions whose timestamp was merely touched have no messages from that day and produce no output
- If the final `total_chars` exceeds 100,000, split the files across Explore subagents to summarize. Otherwise, Read them all yourself

## 2. List the insights

From what you read, list the new insights the user gained as bullet points grouped by topic.

- Pick up facts and decisions reusable next time, not a log of work done
- Mark unverified content as "unverified" or "guess"
- Mark items already recorded in memory (`MEMORY.md`)

## 3. Narrow to 3 themes and let the user choose

Present 3 options with AskUserQuestion, chosen by these criteria:

- Useful or interesting to IT engineers outside the company
- No internal architecture, ticket numbers, PR numbers, costs, or personal names. Drop candidates that would reveal them
- If a candidate includes unverified claims, say "unverified" in its description

## 4. Write the draft

Write it as a narrative tweet, not a numbered how-to list. Write the tweet in Japanese.

- Open with the problem or what triggered the discovery, and close with the insight
- Put commands inline in the sentence. Keep required arguments and permissions so readers can try them as-is
- For anything you have not verified yourself, hedge with "らしい" instead of asserting it
- Stick to one topic. Write side notes outside the draft as reply material
- Put a half-width space between Japanese text and half-width alphanumerics

Do not count characters by eye. Count with Python and keep it within 140. Half-width characters also count as 1.

```bash
python -I -c "print(len('''<draft>'''))"
```

## 5. Output

Show the draft in a `text` code block with its character count.
Then briefly note what changed from the source material and what to check before posting (unverified steps, details that did not fit).

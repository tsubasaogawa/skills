---
name: hacker-news-digest-ja
description: "Generate a Japanese digest for yesterday's Hacker News stories scoring over 100 points, matching the `main.py` workflow without `google-generativeai` or `GEMINI_API_KEY`. Use this skill when users ask for a daily HN digest, want top Hacker News posts translated and summarized in Japanese, or want the Gemini-based workflow replaced with a skill."
metadata:
  version: 0.1.0
---

# Hacker News digest in Japanese

Use this skill to reproduce the current `main.py` behavior in a reusable way, but rely on the model's own language abilities instead of Gemini.

## Default scope

Unless the user explicitly asks for something else, keep the behavior fixed to match `main.py`:

- Time window: yesterday in UTC, from `00:00:00` to the next `00:00:00`
- Source: `https://hn.algolia.com/api/v1/search_by_date`
- Filters: `tags=story`, `points>100`
- Page size: `hitsPerPage=100`
- Output: a Markdown table in Japanese

Do not ask for `GEMINI_API_KEY`. Do not use `google-generativeai`.

## Workflow

1. Read `scripts/fetch_hn_stories.py` to confirm the exact fetch logic.
2. Prefer running `uv run python skills/hacker-news-digest-ja/scripts/fetch_hn_stories.py` from the repository root.
3. If `uv` is unavailable, fall back to `python3 skills/hacker-news-digest-ja/scripts/fetch_hn_stories.py`.
4. If shell execution cannot reach the network, reproduce the script's exact URL and filters with the available web-fetching tool instead of changing the behavior.
5. Use the fetched stories as the source of truth. Preserve the order returned by the API.
6. For each story:
   - Keep `original_title` exactly as provided.
   - Write a natural Japanese translation for `japanese_title`.
   - Write a one-sentence Japanese summary for `summary`.
7. Produce the final answer as a Markdown table and nothing else unless the user asks for extra commentary.

## Output format

Use this exact header:

```markdown
| タイトル (原文) | タイトル (日本語訳) | 概要 |
| :--- | :--- | :--- |
```

Then output one row per story in this shape:

```markdown
| [Original title](url) | 日本語訳 | 1 文の要約 |
```

Formatting rules:

- Escape any literal `|` inside cell text as `&#124;`.
- If a story URL is missing, use `#` as the link target.
- Keep the original title in the link text exactly as fetched.
- Keep the summary to one Japanese sentence.
- Do not prepend or append prose around the table unless the user explicitly asks for commentary.

## Quality bar

- Prefer concise, natural Japanese over word-for-word translation.
- Make summaries informative enough that the user can skim the table and understand why the post mattered.
- Do not invent details that are not supported by the title or obvious public context.
- If the fetch step fails, report the error clearly instead of fabricating a digest.

## Typical trigger examples

- "昨日の Hacker News の人気記事を日本語で一覧にして"
- "`main.py` を Gemini なしで使える skill にしたい"
- "HN の 100 点超え記事を訳して 1 行ずつ要約して"

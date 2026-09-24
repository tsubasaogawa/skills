# AI Credit Efficient Review

This skill performs high-signal reviews while conserving AI Credit by adjusting investigation depth to the risk of each change. It avoids over-examining low-risk changes such as documentation and focuses on areas such as authorization, data mutation, and external input.

## When to use it

Use this skill for requests such as:

- "Review this while conserving AI Credit."
- "Give this a lightweight review."
- "Look only for serious issues."

Do not use it for an exhaustive code review or when a dedicated review workflow has already been specified.

## How it works

1. It maps the scope and size of the change at low cost.
2. It investigates only high-impact files and behaviors in depth.
3. It reports only issues it finds, together with supporting evidence.

See [SKILL.md](SKILL.md) for the complete decision criteria and workflow.

# Skill Fork Sync

This interactive skill applies upstream updates to a customized forked skill. It presents upstream and local changes one hunk at a time, so you can choose which changes to adopt without losing your customizations.

## Usage

Provide the upstream, the currently based-on version, and the version to import, in that order.

```text
/skill-fork-sync <owner/repo[/path] | github-url> <old-version> <new-version>
```

For example:

```text
/skill-fork-sync owner/skill-repo v1.2.0 v1.4.0
```

## What it does

1. Identifies the upstream and local fork.
2. Fetches the upstream diff between the specified versions.
3. Shows it alongside locally customized regions.
4. Asks whether to adopt each change and applies only the selected changes.

Do not use it for first-time installation, authoring a new skill, or routine code review. See [SKILL.md](SKILL.md) for supported input forms and constraints.

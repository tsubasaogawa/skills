#!/usr/bin/env python3
"""Create or overwrite a note in an Obsidian vault by writing to the vault directory.

Why this script exists: the note body must reach the vault losslessly, and the
`obsidian` CLI cannot carry it. Its `content=` parameter expands `\\n` and `\\t`
and offers no way to escape a backslash, and pushing a multi-kilobyte argument
through the CLI has been observed to crash Obsidian's main process outright
(a malformed IPC payload triggers an unguarded `JSON.parse`). So the body is
never handed to the CLI: this script resolves the vault's filesystem path and
writes the file itself. Nothing is escaped, so nothing can be corrupted.

The CLI is still used, with small arguments only, to look up the vault registry
and to nudge a running Obsidian into opening the new note. Both are optional:
when the CLI is unavailable or Obsidian is not running, the registry is read
from `obsidian.json` and the note is picked up by Obsidian's file watcher the
next time it starts.

Usage:
  obsidian_stock.py create    --title "<session summary>" --body <file> [--config <path>] [--timestamp YYYYMMDD_HHMM] [--vault <name>]
  obsidian_stock.py overwrite --path "<vault-relative path>" --body <file> [--config <path>] [--vault <name>]

`artifacts.directory` is always a vault-relative folder path (empty means the
vault root). `--vault` names the vault to save into directly. It overrides the
config's `vault_name`, which itself overrides falling back to whichever vault
Obsidian currently has focused (see `resolve_vault`).

Both subcommands print `vault<TAB><name>` and `path<TAB><vault-relative path>`.
"""

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
import tomllib
from datetime import datetime

# Windows defaults stdout/stderr and subprocess pipes to the cp932 locale
# encoding, which can't represent every character the `obsidian` CLI or this
# script itself may emit. Force UTF-8 everywhere so the script never crashes
# on decode/encode regardless of the platform's default encoding.
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

DEFAULT_CONFIG = pathlib.Path.home() / ".config" / "session-stocker" / "config.toml"

# Characters Obsidian and/or common filesystems reject in note names.
UNSAFE_CHARS = r'[\\/:*?"<>|#^\[\]]'

# Obsidian dies on oversized CLI arguments, so refuse to send one. Every call
# this script makes is a short lookup; anything larger is a bug worth failing on
# rather than risking the user's editor.
MAX_ARG_BYTES = 4096


def die(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)


def obsidian(*args: str, soft: bool = False) -> str:
    """Run the CLI. With soft=True, failures return an empty string instead of exiting."""
    for arg in args:
        if len(arg.encode("utf-8")) > MAX_ARG_BYTES:
            die(
                f"refusing to pass a {len(arg.encode('utf-8'))}-byte argument to the "
                f"`obsidian` CLI (limit {MAX_ARG_BYTES}): large arguments can crash Obsidian. "
                "Note bodies must be written to the vault directly, never through the CLI."
            )
    try:
        proc = subprocess.run(
            ["obsidian", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
    except FileNotFoundError:
        if soft:
            return ""
        die("`obsidian` CLI not found in PATH. Is the Obsidian CLI installed?")
    except subprocess.TimeoutExpired:
        if soft:
            return ""
        die("`obsidian` CLI timed out. Is Obsidian running?")
    out = proc.stdout.strip()
    failed = proc.returncode != 0 or out.startswith("Error:")
    if failed:
        if soft:
            return ""
        detail = (proc.stderr or proc.stdout).strip()
        die(f"`obsidian {' '.join(args)}` failed: {detail or 'unknown error'}")
    return out


def read_body(path: str) -> str:
    body = pathlib.Path(path).read_text(encoding="utf-8").replace("\r\n", "\n")
    if not body.strip():
        die(f"body file is empty: {path}")
    return body


def to_local_path(raw: str) -> pathlib.Path:
    """Translate a vault path from the registry into one this process can write to.

    Obsidian may report a Windows path (`C:\\Users\\...`) while this script runs
    under WSL, where the same directory is reachable via `/mnt/c/...`.
    """
    if re.match(r"^[A-Za-z]:[\\/]", raw):
        try:
            converted = subprocess.run(
                ["wslpath", "-u", raw],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=10,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            converted = None
        if converted is not None and converted.returncode == 0 and converted.stdout.strip():
            return pathlib.Path(converted.stdout.strip())
    return pathlib.Path(raw)


def registry_files() -> list[pathlib.Path]:
    """Candidate locations of Obsidian's `obsidian.json` vault registry."""
    candidates = [pathlib.Path.home() / ".config" / "obsidian" / "obsidian.json"]
    appdata = os.environ.get("APPDATA")
    if appdata:
        candidates.append(pathlib.Path(appdata) / "obsidian" / "obsidian.json")
    candidates.extend(pathlib.Path("/mnt/c/Users").glob("*/AppData/Roaming/obsidian/obsidian.json"))
    return [c for c in candidates if c.is_file()]


def vaults_from_registry() -> list[tuple[str, str]]:
    """Read the vault registry from disk, so a stopped Obsidian is not fatal.

    The registry stores paths but no names; Obsidian names a vault after its
    directory, so the basename is the name.
    """
    vaults = []
    for registry in registry_files():
        try:
            data = json.loads(registry.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for entry in data.get("vaults", {}).values():
            path = entry.get("path", "").strip()
            if path:
                vaults.append((pathlib.PurePath(path.replace("\\", "/")).name, path))
    return vaults


def list_vaults() -> list[tuple[str, str]]:
    """Known vaults as (name, path), from the CLI when it answers, else from disk."""
    vaults = []
    for line in obsidian("vaults", "verbose", soft=True).splitlines():
        if "\t" not in line:
            continue
        name, path = line.split("\t", 1)
        vaults.append((name.strip(), path.strip()))
    return vaults or vaults_from_registry()


def active_vault_name() -> str:
    """Name of the vault Obsidian currently has focused.

    Queried by omitting `vault=` from the CLI call, which makes it fall back
    to the most recently focused vault (see `rules/obsidian.md`).
    """
    name = obsidian("vault", "info=name", soft=True).strip()
    if not name:
        die(
            "no `vault_name` is configured and the currently active Obsidian vault "
            "could not be determined. Either start Obsidian with a vault open, set "
            "`vault_name` in the config, or pass --vault."
        )
    return name


def resolve_vault(
    config_path: pathlib.Path, vault_override: str | None = None
) -> tuple[str, pathlib.Path, str]:
    """Return (vault name, vault directory, vault-relative folder).

    `artifacts.directory` is always a folder path relative to the vault root
    (empty means the vault root itself) -- never an absolute filesystem path.
    The vault comes from `vault_override` or the config's `vault_name` when
    either is set; otherwise it falls back to whichever vault Obsidian
    currently has focused.
    """
    if not config_path.exists():
        die(f"config not found: {config_path}")
    config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    artifacts = config.get("artifacts", {})
    directory = artifacts.get("directory", "").strip()
    vault_name = vault_override or artifacts.get("vault_name", "").strip() or active_vault_name()

    vaults = list_vaults()
    match = next((path for name, path in vaults if name == vault_name), None)
    if match is None:
        listing = "\n".join(f"  {n}\t{p}" for n, p in vaults) or "  (none)"
        die(f"vault {vault_name!r} not found.\nknown vaults:\n{listing}")

    vault_dir = to_local_path(match)
    if not vault_dir.is_dir():
        die(f"vault {vault_name!r} resolves to {vault_dir}, which is not a readable directory")

    return vault_name, vault_dir, directory.strip("/")


def sanitize(title: str) -> str:
    """Keep the title readable while dropping characters Obsidian rejects."""
    cleaned = re.sub(UNSAFE_CHARS, " ", title)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    if not cleaned:
        die(f"title became empty after sanitizing: {title!r}")
    return cleaned


def reveal(vault: str, note_path: str) -> None:
    """Best-effort nudge so a running Obsidian opens the note immediately.

    Obsidian's file watcher indexes the note either way, so a failure here says
    nothing about whether the write succeeded and must never be fatal.
    """
    obsidian(f"vault={vault}", "open", f"path={note_path}", soft=True)


def write_note(vault: str, vault_dir: pathlib.Path, note_path: str, body: str, overwrite: bool) -> None:
    target = vault_dir / note_path
    if target.exists() and not overwrite:
        die(f"note already exists: {target}")
    if overwrite and not target.exists():
        die(f"note to overwrite does not exist: {target}")

    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)

    stored = target.read_text(encoding="utf-8")
    if stored != body:
        die(
            f"round-trip check failed for {target}: the file on disk differs from the "
            "body that was written."
        )

    reveal(vault, note_path)
    print(f"vault\t{vault}")
    print(f"path\t{note_path}")


def cmd_create(args: argparse.Namespace) -> None:
    body = read_body(args.body)
    vault, vault_dir, folder = resolve_vault(pathlib.Path(args.config), args.vault)
    stamp = args.timestamp or datetime.now().strftime("%Y%m%d_%H%M")
    base = f"{stamp}_{sanitize(args.title)}"

    target_dir = vault_dir / folder if folder else vault_dir
    name = f"{base}.md"
    suffix = 2
    while (target_dir / name).exists():
        name = f"{base}-{suffix}.md"
        suffix += 1

    prefix = f"{folder}/" if folder else ""
    write_note(vault, vault_dir, f"{prefix}{name}", body, overwrite=False)


def cmd_overwrite(args: argparse.Namespace) -> None:
    body = read_body(args.body)
    vault, vault_dir, _ = resolve_vault(pathlib.Path(args.config), args.vault)
    write_note(vault, vault_dir, args.path.strip("/"), body, overwrite=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create", help="create a new note from a body file")
    create.add_argument("--title", required=True, help="session summary used in the filename")
    create.add_argument("--body", required=True, help="file holding the Markdown body")
    create.add_argument("--config", default=str(DEFAULT_CONFIG))
    create.add_argument("--timestamp", help="override the YYYYMMDD_HHMM prefix")
    create.add_argument(
        "--vault", help="save into this vault by name, overriding vault_name / the active-vault fallback"
    )
    create.set_defaults(func=cmd_create)

    over = sub.add_parser("overwrite", help="replace the contents of an existing note")
    over.add_argument("--path", required=True, help="vault-relative note path")
    over.add_argument("--body", required=True, help="file holding the Markdown body")
    over.add_argument("--config", default=str(DEFAULT_CONFIG))
    over.add_argument(
        "--vault", help="save into this vault by name, overriding vault_name / the active-vault fallback"
    )
    over.set_defaults(func=cmd_overwrite)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

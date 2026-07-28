#!/usr/bin/env python3
"""Create or overwrite a note in an Obsidian vault through the `obsidian` CLI.

Why this script exists: the CLI takes note bodies as a `content=` argument in which
`\\n` and `\\t` are expanded into newline and tab, and there is no way to escape a
backslash. Passing a transcript straight through would silently corrupt anything
containing a literal backslash (Windows paths, regexes, code with `\\n` in strings).

To stay lossless, the body's backslashes are swapped for a private-use placeholder
before `create`, then restored inside Obsidian via `eval`, and the result is read
back and compared against the original. The CLI is invoked through argv, never a
shell, so quotes, backticks and `$` need no handling at all.

Usage:
  obsidian_stock.py create    --title "<session summary>" --body <file> [--config <path>] [--timestamp YYYYMMDD_HHMM]
  obsidian_stock.py overwrite --path "<vault-relative path>" --body <file> [--config <path>]

Both subcommands print `vault<TAB><name>` and `path<TAB><vault-relative path>`.
"""

import argparse
import pathlib
import re
import subprocess
import sys
import tomllib
from datetime import datetime

DEFAULT_CONFIG = pathlib.Path.home() / ".config" / "session-stocker" / "config.toml"

# Characters Obsidian and/or common filesystems reject in note names.
UNSAFE_CHARS = r'[\\/:*?"<>|#^\[\]]'

# Private-use codepoint that stands in for a backslash while the body travels
# through the CLI's `content=` escaping.
PLACEHOLDER = "\ue000"


def die(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)


def obsidian(*args: str, soft: bool = False) -> str:
    """Run the CLI. With soft=True, failures return an empty string instead of exiting."""
    try:
        proc = subprocess.run(
            ["obsidian", *args], capture_output=True, text=True, timeout=120
        )
    except FileNotFoundError:
        die("`obsidian` CLI not found in PATH. Is the Obsidian CLI installed?")
    except subprocess.TimeoutExpired:
        die("`obsidian` CLI timed out. Is Obsidian running?")
    out = proc.stdout.strip()
    failed = proc.returncode != 0 or out.startswith("Error:")
    if failed:
        if soft:
            return ""
        detail = (proc.stderr or proc.stdout).strip()
        die(f"`obsidian {' '.join(args)}` failed: {detail or 'unknown error'}")
    return out


def normalize_path(raw: str) -> str:
    """Normalize a Windows or WSL path into a comparable `c:/foo/bar` form."""
    p = raw.strip().replace("\\", "/").rstrip("/")
    mount = re.match(r"^/mnt/([A-Za-z])(/.*)?$", p)
    if mount:
        p = f"{mount.group(1)}:{mount.group(2) or ''}"
    return p.lower()


def read_body(path: str) -> str:
    body = pathlib.Path(path).read_text(encoding="utf-8").replace("\r\n", "\n")
    if not body.strip():
        die(f"body file is empty: {path}")
    if PLACEHOLDER in body:
        die("body contains U+E000, which this script reserves as an escape placeholder")
    return body


def encode_content(body: str) -> str:
    """Make the body survive `content=`: no backslashes, real newlines/tabs escaped."""
    return body.replace("\\", PLACEHOLDER).replace("\t", "\\t").replace("\n", "\\n")


def resolve_vault(config_path: pathlib.Path) -> tuple[str, str]:
    """Return (vault name, vault-relative folder) for `artifacts.directory`."""
    if not config_path.exists():
        die(f"config not found: {config_path}")
    config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    directory = config.get("artifacts", {}).get("directory", "").strip()
    if not directory:
        die(f"`artifacts.directory` is not set in {config_path}")

    target = normalize_path(directory)
    vaults = []
    for line in obsidian("vaults", "verbose").splitlines():
        if "\t" not in line:
            continue
        name, path = line.split("\t", 1)
        vaults.append((name.strip(), path.strip()))

    matches = [
        (name, path)
        for name, path in vaults
        if target == normalize_path(path) or target.startswith(normalize_path(path) + "/")
    ]
    if not matches:
        listing = "\n".join(f"  {n}\t{p}" for n, p in vaults) or "  (none)"
        die(
            f"artifacts.directory ({directory}) is not inside any known vault.\n"
            f"known vaults:\n{listing}"
        )
    # Longest match wins so a nested vault beats its parent.
    name, path = max(matches, key=lambda m: len(normalize_path(m[1])))
    folder = target[len(normalize_path(path)) :].strip("/")
    return name, folder


def sanitize(title: str) -> str:
    """Keep the title readable while dropping characters Obsidian rejects."""
    cleaned = re.sub(UNSAFE_CHARS, " ", title)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    if not cleaned:
        die(f"title became empty after sanitizing: {title!r}")
    return cleaned


def existing_names(vault: str, folder: str) -> set[str]:
    args = [f"vault={vault}", "files"]
    if folder:
        args.append(f"folder={folder}")
    listing = obsidian(*args, soft=True)
    return {line.strip().rsplit("/", 1)[-1] for line in listing.splitlines() if line.strip()}


def restore_backslashes(vault: str, note_path: str) -> None:
    """Swap the placeholder back to a real backslash from inside Obsidian.

    The CLI does not reliably echo an async eval's return value, so success is not
    judged here — `verify()` compares the stored note against the body instead.
    """
    js = (
        "(async()=>{"
        f"const f=app.vault.getAbstractFileByPath({js_str(note_path)});"
        "if(!f)return 'missing';"
        "const s=await app.vault.read(f);"
        "await app.vault.modify(f,s.split(String.fromCharCode(57344))"
        ".join(String.fromCharCode(92)));"
        "return 'ok';})()"
    )
    obsidian(f"vault={vault}", "eval", f"code={js}", soft=True)


def js_str(value: str) -> str:
    """JS string literal built without backslashes, which `content=`/`code=` would eat."""
    return "String.fromCharCode(" + ",".join(str(ord(c)) for c in value) + ")"


def matches(vault: str, note_path: str, body: str) -> bool:
    stored = obsidian(f"vault={vault}", "read", f"path={note_path}", soft=True)
    return stored.replace("\r\n", "\n").strip() == body.strip()


def write_note(vault: str, note_path: str, body: str, overwrite: bool) -> None:
    args = [f"vault={vault}", "create", f"path={note_path}", f"content={encode_content(body)}"]
    if overwrite:
        args.append("overwrite")
    obsidian(*args)

    if "\\" in body:
        for _ in range(2):
            restore_backslashes(vault, note_path)
            if matches(vault, note_path, body):
                break
    if not matches(vault, note_path, body):
        die(
            f"round-trip check failed for {note_path}: the stored note differs from the "
            "body that was sent. Inspect the note in Obsidian before trusting it."
        )
    print(f"vault\t{vault}")
    print(f"path\t{note_path}")


def cmd_create(args: argparse.Namespace) -> None:
    body = read_body(args.body)
    vault, folder = resolve_vault(pathlib.Path(args.config))
    stamp = args.timestamp or datetime.now().strftime("%Y%m%d_%H%M")
    base = f"{stamp}_{sanitize(args.title)}"

    taken = existing_names(vault, folder)
    name = f"{base}.md"
    suffix = 2
    while name in taken:
        name = f"{base}-{suffix}.md"
        suffix += 1

    prefix = f"{folder}/" if folder else ""
    write_note(vault, f"{prefix}{name}", body, overwrite=False)


def cmd_overwrite(args: argparse.Namespace) -> None:
    body = read_body(args.body)
    vault, _ = resolve_vault(pathlib.Path(args.config))
    write_note(vault, args.path, body, overwrite=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create", help="create a new note from a body file")
    create.add_argument("--title", required=True, help="session summary used in the filename")
    create.add_argument("--body", required=True, help="file holding the Markdown body")
    create.add_argument("--config", default=str(DEFAULT_CONFIG))
    create.add_argument("--timestamp", help="override the YYYYMMDD_HHMM prefix")
    create.set_defaults(func=cmd_create)

    over = sub.add_parser("overwrite", help="replace the contents of an existing note")
    over.add_argument("--path", required=True, help="vault-relative note path")
    over.add_argument("--body", required=True, help="file holding the Markdown body")
    over.add_argument("--config", default=str(DEFAULT_CONFIG))
    over.set_defaults(func=cmd_overwrite)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

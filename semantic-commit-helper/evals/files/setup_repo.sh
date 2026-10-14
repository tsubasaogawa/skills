#!/usr/bin/env bash
# Usage: setup_repo.sh <case> <dir>
set -euo pipefail
case_name=$1
dir=$2
rm -rf "$dir"
mkdir -p "$dir"
git -C "$dir" init -q
git -C "$dir" config user.name eval
git -C "$dir" config user.email eval@example.com

commit_base() {
  git -C "$dir" add -A
  git -C "$dir" commit -qm "chore: initial commit"
}

case $case_name in
  typo)
    printf '# demo\n\n## Instalation\n\nRun `npm install`.\n' > "$dir/README.md"
    commit_base
    sed -i 's/Instalation/Installation/' "$dir/README.md"
    git -C "$dir" add README.md
    ;;
  deps)
    printf '{\n  "name": "demo",\n  "dependencies": {\n    "lodash": "4.17.20"\n  }\n}\n' > "$dir/package.json"
    commit_base
    sed -i 's/4.17.20/4.17.21/' "$dir/package.json"
    git -C "$dir" add package.json
    ;;
  ambiguous)
    mkdir -p "$dir/src"
    printf 'export const TIMEOUT_MS = 30000;\nexport const MAX_RETRIES = 3;\n\nexport async function fetchJson(url) {\n  const res = await fetch(url, { signal: AbortSignal.timeout(TIMEOUT_MS) });\n  return res.json();\n}\n' > "$dir/src/client.js"
    commit_base
    sed -i 's/30000/60000/; s/MAX_RETRIES = 3/MAX_RETRIES = 5/' "$dir/src/client.js"
    git -C "$dir" add src/client.js
    ;;
  feature)
    mkdir -p "$dir/src"
    printf 'export function add(a, b) {\n  return a + b;\n}\n' > "$dir/src/util.js"
    commit_base
    printf '\nexport function formatDate(date) {\n  return date.toISOString().slice(0, 10);\n}\n' >> "$dir/src/util.js"
    git -C "$dir" add src/util.js
    ;;
  unstaged)
    printf 'hello\n' > "$dir/notes.txt"
    commit_base
    printf 'hello world\n' > "$dir/notes.txt"
    ;;
  large)
    mkdir -p "$dir/src"
    for i in $(seq 1 12); do printf 'var value%s = 1;\n' "$i" > "$dir/src/mod$i.js"; done
    commit_base
    for i in $(seq 1 12); do
      { printf 'const value%s = 1;\n' "$i"; for j in $(seq 1 30); do printf 'export const v%s_%s = %s;\n' "$i" "$j" "$j"; done; } > "$dir/src/mod$i.js"
    done
    git -C "$dir" add -A
    ;;
  *)
    echo "unknown case: $case_name" >&2
    exit 1
    ;;
esac

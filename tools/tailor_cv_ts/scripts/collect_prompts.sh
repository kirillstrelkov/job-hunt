#!/usr/bin/env bash
set -euo pipefail

PROMPTS_DIR="$(cd "$(dirname "$0")/../prompts" && pwd)"
OUT="${1:-tmp/combined_prompts.md}"
mkdir -p "$(dirname "$OUT")"

> "$OUT"

for f in "$PROMPTS_DIR"/*.txt; do
  name="$(basename "$f" .txt)"
  printf '# %s\n\n```\n' "$name" >> "$OUT"
  cat "$f" >> "$OUT"
  printf '\n```\n\n' >> "$OUT"
done

echo "Wrote $OUT"

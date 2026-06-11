#!/usr/bin/env bash
set -euo pipefail

# ── Configuration ──────────────────────────────────────────────────────────────
CV="/home/kirill/MEGAsync/etc/cv/mastercv.md"
JD="/home/kirill/MEGAsync/etc/cv/tmp/nvidia.txt"
OUT_DIR="tmp"

MODELS=(
    "gemma4:e2b",
    "llama3.1:8b",
    "deepseek-r1:7b",
    "qwen2.5:7b",
)
# ──────────────────────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ ! -f "$CV" ]]; then
  echo "Error: master CV not found at $CV" >&2
  exit 1
fi
if [[ ! -f "$JD" ]]; then
  echo "Error: job description not found at $JD" >&2
  exit 1
fi

mkdir -p "$ROOT/$OUT_DIR"

for model_raw in "${MODELS[@]}"; do
  model="${model_raw%,}"                 # strip trailing comma (allows JS-style list)
  safe="${model//[:\/]/_}"
  out="$ROOT/$OUT_DIR/${safe}.pdf"
  echo "── $model → $OUT_DIR/${safe}.pdf"
  (cd "$ROOT" && npx tsx cli.ts -i "$CV" -j "$JD" -o "$out" -m "$model")
done

echo ""
echo "── Collecting prompts"
bash "$SCRIPT_DIR/collect_prompts.sh" "$ROOT/$OUT_DIR/combined_prompts.md"

echo "── Building summary.md"
SUMMARY="$ROOT/$OUT_DIR/summary.md"
> "$SUMMARY"
for f in "$ROOT/$OUT_DIR"/*.md; do
  [[ "$(basename "$f")" == "summary.md" ]] && continue
  name="$(basename "$f" .md)"
  printf '# %s\n\n' "$name" >> "$SUMMARY"
  cat "$f" >> "$SUMMARY"
  printf '\n\n---\n\n' >> "$SUMMARY"
done

echo ""
echo "Done. Outputs in $ROOT/$OUT_DIR/"
echo "  summary.md combines all .md files"

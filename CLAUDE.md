# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository overview

Three independent tools for AI-assisted CV tailoring, each solving the same problem in a different stack. No shared code between them.

| Tool                     | Stack                | Entry point                                     |
| ------------------------ | -------------------- | ----------------------------------------------- |
| `tools/prep_for_cv_tail` | Rust + Tauri         | Template renderer + Markdown/PDF desktop editor |
| `tools/tailor_cv_py`     | Python + Streamlit   | CLI + Streamlit UI, Ollama/Gemini               |
| `tools/tailor_cv_ts`     | TypeScript + Next.js | CLI + full web UI, Ollama/Claude/Gemini         |

Each tool has its own `CLAUDE.md` with detailed per-tool guidance.

## Quick commands

### prep_for_cv_tail (Rust)

```bash
cd tools/prep_for_cv_tail
cargo build                     # both binaries
cargo test --lib                # unit tests
cargo run --bin prep_for_tail -- --cv cv.md --prompt prompt.txt --jd jd.txt -o out.md
cargo run --bin prep_for_tail_ui   # Tauri desktop app
```

### tailor_cv_py (Python)

```bash
cd tools/tailor_cv_py
uv sync                         # install deps
uv run pytest                   # all tests
uv run pytest tests/test_pdf.py # single test file
uv run tailor_cv -i cv.txt -j jd.txt -o out.pdf
just ui                         # Streamlit UI
```

### tailor_cv_ts (TypeScript)

```bash
cd tools/tailor_cv_ts
npm install
npm run dev                     # dev server at localhost:3000
npx tsc --noEmit                # type-check
npm run cli -- -i cv.txt -j jd.txt -o out.pdf
```

## Shared architecture

All three tools follow the same data flow:

1. Read master CV + job description from files (or UI state)
2. Convert job description to plain text (strip Markdown/HTML)
3. Format `{cv}` + `{job_description}` into a user prompt template
4. Call LLM with a fixed system prompt → 4-section Markdown output
5. Prepend `default_header.md`, append `default_footer.md`
6. Optionally convert to PDF via `pandoc`

### Prompt system

Six prompt files live under each tool's `prompts/` directory (same content across tools):

- `cv_system.txt` / `cv_user.txt` — CV tailoring
- `cover_letter_system.txt` / `cover_letter_user.txt` — cover letter
- `default_header.md` / `default_footer.md` — static prefix/suffix

The CV system prompt enforces exactly 4 output sections: `## Summary`, `## Technical Skills`, `## Work Experience`, `## Previous Experience`. Date right-alignment uses `\hfill` (LaTeX embedded in Markdown — works through pandoc, breaks plain renderers).

### LLM routing

Model selection is prefix-based: names starting with `gemini` route to Gemini API, `claude`/`anthropic` route to Claude (TypeScript only), anything else goes to local Ollama. Default model is `gemma4:e2b`.

### PDF generation

All tools shell out to `pandoc` for Markdown → PDF. `prep_for_cv_tail` falls back to `wkhtmltopdf`. Pandoc must be on `$PATH` — desktop/GUI-launched processes may not inherit shell PATH; the Tauri UI explicitly prepends `/usr/local/bin:/usr/bin:/bin`.

## System dependencies

- **pandoc** — required for PDF output in all tools
- **Ollama** running locally — `ollama pull gemma4:e2b` for default model
- **LaTeX** (pdflatex/xelatex) — required by pandoc for PDF rendering
- Tauri Linux deps: `libwebkit2gtk-4.1-dev libwayland-dev libssl-dev libgtk-3-dev libayatana-appindicator3-dev librsvg2-dev`

## Tool / Assistant Rules

- **Ignored Files**: Never read, write, or modify files matched by `.antigravityignore` without asking for explicit user confirmation first, even if directly requested.

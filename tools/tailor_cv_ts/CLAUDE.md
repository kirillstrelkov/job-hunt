# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
just dev          # start Next.js dev server
just build        # production build
just typecheck    # tsc --noEmit (only static validation — no test suite exists)
just cli -- -i cv.txt -j jd.txt -o out.pdf   # run CLI directly
```

**Runtime dependency:** `pandoc` must be installed system-wide for PDF generation.

## What This Does

TailorCV takes a master CV + job description, sends them to an LLM, and produces an ATS-optimized tailored resume (and optional cover letter) in Markdown and/or PDF.

Two interfaces, same core logic:

- **CLI** (`cli.ts`) — reads files from disk, writes `.md`/`.pdf` output. Supports Ollama and Gemini only (no Claude).
- **Web UI** (`app/`) — Next.js App Router single-page app, posts to `/api/tailor`. Supports Ollama, Gemini, and Claude.

## Architecture

**Data flow (web path):**
```
Browser state → POST /api/tailor (all prompts + content inlined)
  → toPlainText(jobDesc) → template substitution → callLlm()
  → header.md + LLM body + footer.md assembled
  → pandoc writes to /tmp/tailor_cv/ → read back as base64
  → { cvMd, cvPdf, covMd?, covPdf? } returned to browser
  → ReactMarkdown render + <iframe src="data:application/pdf;base64,...">
```

**LLM routing (API routes):** model prefix determines provider:

- `model.startsWith("gemini")` → `callGemini` (`src/llm_gemini.ts`)
- `model.startsWith("claude")` → `callClaude` (`src/llm_claude.ts`)
- anything else → `callOllama` (`src/llm.ts`)

API keys (`geminiApiKey`, `claudeApiKey`) can be sent in the request body; the route handler assigns them to `process.env` at request time, overriding any env defaults.

**Prompt system:** Six plain-text files in `/prompts/`. Templates use `{cv}` and `{job_description}` as string placeholders — no template engine. The LLM CV output is expected to have exactly four `##` sections: Summary, Technical Skills, Work Experience, Previous Experience. The final document is assembled as `default_header.md` + LLM body + `default_footer.md`.

**Prompts are editable at runtime** in the web UI's Prompts tab — all templates are loaded from `/api/prompts` on mount and held in React state, so changes are per-session only.

## Key Source Files

- `src/llm.ts` — Ollama client (temp=0.2, top_k=40, top_p=0.85, repeat_penalty=1.15, 4096 tokens, 8192 ctx)
- `src/llm_gemini.ts` — Gemini client (temp=0.2, topK=40, topP=0.85, 8192 tokens)
- `src/llm_claude.ts` — Claude client; uses ephemeral prompt caching on the system prompt. Opus 4.7 requires stripping temperature/top_k/top_p from the request (the API returns 400 if they're sent); earlier Claude models accept temperature=0.
- `src/pdf.ts` — thin wrapper around `pandoc --pdf-engine=xelatex` (GFM → PDF, 1.5cm margins)
- `src/text.ts` — Markdown/HTML → plain text (applied to job description only, not CV)
- `src/prompt.ts` — loads prompt files at module init, exports builder functions
- `src/logger.ts` — colored stderr logger; writes to stderr so stdout stays clean for piping
- `src/tmpdir.ts` — ensures `/tmp/tailor_cv/` exists on module load; shared by CLI and API
- `app/api/tailor/route.ts` — main API route; `maxDuration = 300` for long Vercel calls
- `app/api/cover/route.ts` — standalone cover-letter endpoint
- `app/api/pdf/route.ts` — generic Markdown → PDF converter
- `app/api/prompts/route.ts` — returns all 6 prompt/template files as JSON
- `app/page.tsx` — entire web UI (~814 lines), all state in React ("use client")

## Web UI Structure

Four tabs: **Main**, **Input**, **Prompts**, **Settings**.

- **Main** — model selector, action buttons, resizable split-panel: Markdown editor (markdown/preview sub-tabs) on the left, PDF `<iframe>` on the right, collapsible cover-letter sidebar on the far right.
- **Input** — editable textareas for header/footer, master CV, and job description. Accepts `.txt`/`.md` file uploads.
- **Prompts** — all 4 system/user templates editable per-session.
- **Settings** — JSON editor for `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, and the model list array. Validated with `JSON.parse` on render.

## Non-Obvious Details

- The CLI writes `.md` first even when `--output` ends in `.pdf` — the path extension is swapped, pandoc converts, both files end up on disk.
- `toPlainText()` is applied to the job description only — the master CV keeps its Markdown for the LLM.
- Job date right-alignment uses `\hfill` (LaTeX embedded in Markdown) — works through pandoc but breaks plain Markdown renderers.
- `serverExternalPackages: ["ollama"]` in `next.config.ts` — required because `ollama` uses native Node.js modules incompatible with Next.js webpack bundling.
- No tests, no linter — `just typecheck` is the only automated quality gate.
- Temporary files are named with `Date.now()` (e.g. `tailor_1234567890.md`) and cleaned up in a `finally` block in the API route.

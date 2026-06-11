# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```sh
cargo build                    # build both binaries
cargo test --lib               # run unit tests (lib.rs)
cargo run --bin prep_for_tail -- --cv cv.md --prompt prompt.txt --jd jd.txt -o out.md
cargo run --bin prep_for_tail_ui   # launch Tauri desktop app
```

**No system PDF tools required** — PDF generation is pure Rust (Typst). The Tauri UI itself needs:

```sh
sudo apt-get install -y \
  libwebkit2gtk-4.1-dev libwayland-dev libssl-dev \
  libgtk-3-dev libayatana-appindicator3-dev librsvg2-dev
```

## Architecture

Two binaries share a common library:

- **`src/lib.rs`** — `DEFAULT_TEMPLATE` and `render_template(template, prompt, cv, jd) -> String`. Template format:
  ```
  {prompt text}
  <cv>
  {master cv}
  </cv>
  <job_description>
  {job description}
  </job_description>
  ```
- **`src/main.rs`** → `prep_for_tail` (CLI). Reads `--cv`, `--prompt`, `--jd` files, calls `render_template`, writes `-o` output.
- **`src/bin/ui.rs`** → `prep_for_tail_ui` (Tauri desktop app).

## Tauri UI

**Backend** (`src/bin/ui.rs`): seven `#[tauri::command]` functions —

| Command | Purpose |
|---------|---------|
| `render_markdown` | Markdown → HTML via comrak (for Preview tabs) |
| `convert_to_pdf` | Markdown → PDF via Typst, returns base64 |
| `save_pdf` | Copies `$TMPDIR/prep_for_tail_current.pdf` to user-chosen path |
| `pick_save_path` | Native save dialog for PDF, returns path |
| `load_markdown_file` | Native open dialog, returns file text |
| `save_text` | Native save dialog, writes text content |
| `load_yaml_config` | Opens YAML, resolves paths, returns `{ header, body, footer, prompt }` |

**Frontend** (`web/`): vanilla HTML/CSS/JS, no bundler. Three-tab interface:

- **Tab 1 (MD → PDF)**: Markdown editor + Preview pane (left); PDF `<iframe>` (right). Convert to PDF button calls `convert_to_pdf` → base64 data URL embedded in iframe.
- **Tab 2 (CV Settings)**: Header/Body/Footer section editors with Edit/Preview each (left); Master CV editor with Load button in tab bar (right). Combine button joins non-empty sections.
- **Tab 3 (LLM Settings)**: Master CV (read-only sync from Tab 2) / Job Desc / Prompt tabs (left); generated LLM prompt output (right). Master CV is synced on tab switch.

## PDF Engine

Pure Rust: `typst-as-lib` compiles a Typst document; `typst-pdf` exports it to bytes. The Markdown → Typst conversion (`markdown_to_typst` in `ui.rs`) handles:

- Headings → Typst `=` / `==` / `===` markers
- `\hfill` → `#h(1fr)` (right-aligns dates in the same line)
- `\newpage` (in a lone paragraph) → `#pagebreak()`
- Task-list checkboxes → `☐`/`☑` glyphs
- Thematic breaks → `#line(length: 100%)`
- Typst special characters escaped: `# @ _ * \` ` $ [ ] { } ~ \`

Font stack (per-glyph fallback): Linux Libertine → Liberation Sans → DejaVu Sans → Noto Sans. Cyrillic renders via DejaVu/Noto.

## Non-Obvious Details

- `build.rs` calls `tauri_build::build()` for every `cargo build` — this also runs for the CLI binary and is harmless.
- The `tauri.conf.json` `withGlobalTauri: true` exposes `window.__TAURI__` globally so `app.js` can call `invoke` without an ES module import.
- `capabilities/default.json` only grants `core:default`. The clipboard write in Tab 3 uses `navigator.clipboard` (browser API), not a Tauri plugin — CSP is set to `null` to allow this.
- The YAML config resolves paths relative to the YAML file's directory. Absolute paths are also accepted; any of the four keys can be absent.
- `prompt-editor` (Tab 2 YAML-loaded prompt) and `prompt-editor` (Tab 3 Load Prompt) share the same `<textarea id="prompt-editor">` — loading a prompt in either place fills the same element, which appears in both Tab 2 YAML load and Tab 3 left panel.

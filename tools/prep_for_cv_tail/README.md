# prep_for_cv_tail

A Rust + Tauri desktop tool for CV preparation. Converts Markdown to PDF and assembles LLM prompts for CV tailoring — no external binaries required.

## Binaries

| Binary | Description |
|--------|-------------|
| `prep_for_tail` | CLI: combines CV + prompt + job description into a single Markdown file |
| `prep_for_tail_ui` | Desktop GUI (Tauri) |

## Desktop UI

Three-tab interface for the full CV tailoring workflow.

### Tab 1 — MD → PDF

Convert any Markdown document to PDF.

- **Load Markdown…** — open a `.md`/`.txt` file into the editor
- **Markdown / Preview** tabs — edit raw Markdown on the left; switch to Preview to see rendered HTML
- **Convert to PDF** — renders the Markdown to PDF (pure Rust, no pandoc) and displays it in the right panel
- **Download PDF** — save the generated PDF to a chosen location

Supported Markdown features: headings, bold/italic, ordered/unordered lists, task-list checkboxes, inline/fenced code, horizontal rules, `\hfill` (right-align text on the same line, useful for date alignment in CVs), `\newpage` (page break), Cyrillic text.

### Tab 2 — CV Settings

Build and manage the Master CV from reusable sections.

**Left panel — Section editors (Header / Body / Footer)**

Each section has an **Edit / Preview** toggle. Write Markdown in Edit mode; switch to Preview to see rendered output.

- **Load Config…** — load a YAML config file that specifies paths to the header, body, footer, and prompt files; all referenced files are loaded automatically
- **Load into active…** — open a Markdown file directly into whichever section tab is currently active (Header, Body, or Footer)
- **Combine → Master CV** — concatenates the non-empty Header, Body, and Footer sections into the Master CV editor on the right

**Right panel — Master CV**

- **Master CV / Preview** tabs — edit the combined CV or preview its rendered output
- **Load…** button (inside the tab bar) — load a Markdown file directly into the Master CV editor, bypassing the section workflow

The Master CV is automatically synced to the LLM Settings tab whenever you switch to it.

### Tab 3 — LLM Settings

Assemble the full prompt to paste into an LLM for CV tailoring.

**Left panel tabs**

| Tab | Content |
|-----|---------|
| Master CV | Read-only mirror of the Master CV from Tab 2 |
| Job Desc | Paste the job description here |
| Prompt | The prompt template (instructions to the LLM) |

**Toolbar**

- **Load Prompt…** — open a text file into the Prompt editor
- **Create LLM Prompt** — combines Prompt + Master CV + Job Description into the output area using the format:
  ```
  {prompt text}
  <cv>
  {master cv}
  </cv>
  <job_description>
  {job description}
  </job_description>
  ```
- **Copy** — copies the generated prompt to the clipboard
- **Save…** — saves the generated prompt to a `.txt`/`.md` file

## YAML Config File

The **Load Config…** button in Tab 2 accepts a YAML file with optional keys pointing to Markdown files:

```yaml
header: path/to/header.md
body:   path/to/body.md
footer: path/to/footer.md
prompt: path/to/prompt.txt
```

Paths are resolved relative to the YAML file's location. Absolute paths are also accepted. Any key can be omitted; only the present keys are loaded.

## CLI

```sh
cargo run --bin prep_for_tail -- \
  --cv master_cv.md \
  --prompt prompt.txt \
  --jd job_description.txt \
  -o output.md
```

Produces a single Markdown file with the prompt, CV, and job description wrapped in XML-style tags, ready to paste into any LLM.

## Build

```sh
# Both binaries
cargo build

# Unit tests
cargo test --lib

# Desktop UI (requires system deps below)
cargo run --bin prep_for_tail_ui
```

### Linux system dependencies

```sh
sudo apt-get install -y \
  libwebkit2gtk-4.1-dev libwayland-dev libssl-dev \
  libgtk-3-dev libayatana-appindicator3-dev librsvg2-dev
```

## PDF Engine

PDF generation is pure Rust (`typst-as-lib` + `typst-pdf`) — no pandoc or wkhtmltopdf required. The font stack used for rendering:

```
Linux Libertine → Liberation Sans → DejaVu Sans → Noto Sans
```

Typst falls back per-glyph, so Cyrillic characters render correctly via DejaVu/Noto when Linux Libertine lacks them.

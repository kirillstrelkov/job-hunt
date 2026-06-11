# tailor_cv

A CLI tool that rewrites your master CV to match a specific job description, using a locally running Ollama LLM.

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) — Python package manager
- [Ollama](https://ollama.com) running locally with a model pulled:
  ```bash
  ollama pull gemma4:e2b
  ```
- [pandoc](https://pandoc.org) (only needed for PDF output):
  ```bash
  # Debian/Ubuntu
  sudo apt install pandoc
  # macOS
  brew install pandoc
  ```

## Installation

```bash
git clone <repo-url>
cd cv_app_gen
uv sync
```

## Usage

```bash
tailor_cv -i master_cv.txt -j job_description.txt -o tailored_cv.pdf
```

### Flags

| Flag | Long form | Required | Default | Description |
|------|-----------|----------|---------|-------------|
| `-i` | `--input` | yes | — | Path to master CV plain text file |
| `-j` | `--job` | yes | — | Path to job description plain text file |
| `-o` | `--output` | yes | — | Output path (`.md` or `.pdf`) |
| `-l` | `--log-level` | no | `INFO` | Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `-m` | `--model` | no | `gemma4:e2b` | Ollama model name |

### Examples

```bash
# Output as Markdown
tailor_cv -i ~/cvs/master.txt -j ~/jobs/senior_dev.txt -o ~/cvs/tailored.md

# Output as PDF
tailor_cv -i ~/cvs/master.txt -j ~/jobs/senior_dev.txt -o ~/cvs/tailored.pdf

# Use a different model with debug logging
tailor_cv -i master.txt -j jd.txt -o out.pdf -m llama3.2 -l DEBUG
```

## Development

```bash
# Install with dev dependencies
uv sync

# Run tests
uv run pytest

# Run the CLI directly
uv run tailor_cv --help
```

## How It Works

1. Reads the master CV and job description from disk
2. Builds a structured recruiter prompt combining both
3. Sends the prompt to the local Ollama model
4. Writes the LLM output as Markdown
5. If the output path ends in `.pdf`, converts via `pandoc`

The LLM is instructed to produce a CV with sections: **Professional Summary**, **Core Skills**, **Professional Experience**, **Highlighted Projects**, and **Education & Certifications**.

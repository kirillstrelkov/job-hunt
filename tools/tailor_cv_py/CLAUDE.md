# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`tailor_cv` is a Python CLI tool that tailors a master CV to a specific job description using a locally running Ollama LLM. It reads both files, sends them to the model with a structured recruiter prompt, and writes the result as Markdown or PDF.

## Tech Stack

- **Python ≥ 3.11**, packaged with [uv](https://github.com/astral-sh/uv) + hatchling
- **typer** — CLI argument parsing
- **loguru** — structured logging
- **ollama** — Python client for local Ollama models
- **pandoc** — Markdown → PDF conversion (system dependency)
- **pytest** + **pytest-mock** — testing

## Project Layout

```text
src/tailor_cv/
  cli.py      # Entry point: parses args, orchestrates flow
  reader.py   # read_file(path) → str
  prompt.py   # build_prompt(cv, jd) → str
  llm.py      # call_ollama(prompt, model) → str
  pdf.py      # convert_to_pdf(md_path, pdf_path) → None
tests/
  test_reader.py
  test_prompt.py
  test_llm.py
  test_pdf.py
```

## Dev Setup

```bash
uv sync           # install all dependencies
uv run pytest     # run tests
uv run tailor_cv --help
```

## CLI Usage

```text
tailor_cv -i <master_cv> -j <job_description> -o <output.[md|pdf]> [-l LOG_LEVEL] [-m MODEL]
```

- `-i` / `--input`  — path to master CV plain text file (required)
- `-j` / `--job`    — path to job description file (required)
- `-o` / `--output` — output path; `.md` writes Markdown, `.pdf` runs pandoc (required)
- `-l` / `--log-level` — log level: DEBUG, INFO, WARNING, ERROR (default: INFO)
- `-m` / `--model`  — Ollama model name (default: `gemma4:e2b`)

## Prerequisites

- [Ollama](https://ollama.com) running locally with the target model pulled (`ollama pull gemma4:e2b`)
- `pandoc` installed for PDF output (`apt install pandoc` / `brew install pandoc`)

# CLAUDE.md

This file provides guidance when working with code in this repository.

## Repository Overview

`job-hunt` is a Python workspace for the job-application pipeline: parsing/validating Markdown Resume schemas, tailoring master Resumes against job descriptions using local (Ollama) or cloud (Gemini) LLMs, scraping job listings from job boards (Indeed, LinkedIn, Stepstone), evaluating role compatibility, and benchmarking LLM output quality.

The Python package lives under `src/job_hunt/`.

## Developer Quick Commands

```bash
uv sync                                    # install deps managed with uv
just install                               # install deps and package in editable mode
just test                                  # run fast unit tests (`tests/unit/`)
just test-integration                      # run integration & browser tests (`tests/integration/`)
just run resume check data/example_resume/body.md  # validate markdown CV
just run resume tailor -r <cv.md> -j <jd.txt> -o <out.md> # tailor CV
just run ui                                # launch Streamlit web app
just lint                                  # ruff format + check --fix
```

## Running CLI from Any Directory (e.g. `/tmp`)

```bash
# Option 1: Editable package install
uv pip install -e .
cd /tmp && job-hunt resume check ./draft_cv.md

# Option 2: via uv run --directory
cd /tmp && uv run --directory /path/to/job-hunt job-hunt resume check ./draft_cv.md
```

## Architecture

- **`src/job_hunt/config/`**: Centralized configuration (`config.py`, `config.yaml`). ConfigManager loads paths and resolves placeholders relative to the repository root.
- **`src/job_hunt/core/`**: Lower-level helpers (`llm_helper.py`, `ollama_helper.py`) and Pydantic AI (`pydantic_ai.Agent`) wrappers (`core/llm/`), OpenTelemetry / Logfire / Arize Phoenix tracing (`core/telemetry.py`).
- **`src/job_hunt/resume/`**: Pydantic models for Markdown Resume parsing/validation (`parser.py`), resume tailoring logic (`tailor.py`), and PDF rendering (`renderer.py`).
- **`src/job_hunt/job_finder/`**: Selenium/`easelenium` scrapers per site (`scraper/`), match reviewer (`reviewer/`), and listing filters.
- **`src/job_hunt/eval/`**: Benchmark framework comparing output quality across DeepEval, Promptfoo, LlamaIndex, Ragas, TruLens, Giskard, etc.
- **`src/job_hunt/ui/`**: Streamlit composer interface (`ui/app.py`).

## Testing Conventions

- **Unit tests** (`tests/unit/`): Fast unit tests without network or browser dependencies.
- **Integration tests** (`tests/integration/`): Tests that interact with live LLMs, external scrapers, or browser drivers.

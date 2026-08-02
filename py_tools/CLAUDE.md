# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`tools/py` is a Python monorepo for the job-hunt Resume-tailoring pipeline: composing/tailoring a master Resume against a job description via local (Ollama) or cloud (Gemini) LLMs, validating/rendering it to PDF, and a separate job-scraping + LLM-matching pipeline. It is a sibling of (not shared code with) `tools/prep_for_cv_tail` (Rust/Tauri) and `tools/tailor_cv_ts` (TypeScript) described in the repo-root `CLAUDE.md` — this directory is the Python implementation and has since grown its own scraper and eval suite beyond what the root doc describes.

## Commands

```bash
uv sync                                          # install deps (Python >=3.12, managed with uv)
uv run pytest -k 'not func'                      # unit tests only (matches `just test`)
uv run pytest path/to/test_file.py               # single test file
uv run pytest path/to/test_file.py::test_name    # single test
just lint                                        # ruff format + check --fix + check
just arize-phoenix                               # start local Arize Phoenix UI for LLM traces
```

Tests named/located under `*func*` (e.g. `tests/func/`, `*_func_test.py`) are functional/integration tests that hit real browsers (Selenium/easelenium) or live LLMs — excluded by default via `-k 'not func'`. Run them explicitly when needed.

Each subdirectory below has its own `justfile` with more specific commands (`resume/justfile`, `job_finder/justfile`, `tailor_resume_eval/justfile`, `ui_composer/justfile`); run `just -l` inside one to see what's available.

### Streamlit UI

```bash
uv run streamlit run ui_composer/app.py
```

### Resume markdown validation

```bash
uv run python md/cli.py resume/example/body.md
```

### Job scraping + LLM matching

```bash
cd job_finder && just fetch-match        # scrape configured URLs, filter via LLM match
cd job_finder && just llm-check-jd       # check a single JD from stdin
```

## Architecture

### Config is centralized and placeholder-resolved

`config/config.yaml` is the single source of truth for LLM model lists/options, file paths, scraper target URLs/filters, and eval job definitions. `config/config.py` (`ConfigManager`) loads it and resolves `{root_dir}`, `{tmp_output_dir}`, etc. placeholders recursively. `helpers/`, `resume/tools/`, `job_finder/`, and `ui_composer/app.py` (via `generate_config()`) all read through this one file rather than hardcoding paths — when changing path/model config, edit `config/config.yaml`, not call sites.

### Two LLM integration layers coexist

- `helpers/llm_helper.py` (Gemini) and `helpers/ollama_helper.py` (Ollama) are the lower-level, config-driven helpers: model option resolution, `run_model()`, GPU/context-window checks.
- `helpers/llm/` (package: `gemini.py`, `ollama.py`, `__init__.py`) is a newer Pydantic AI (`pydantic_ai.Agent`) wrapper built on top of the helpers above (`helpers/llm/ollama.py` imports `get_model_options`/`dict_to_model_settings` from `helpers/llm_helper.py`). It adds typed structured output (`output_type: BaseModel`), OpenTelemetry/Logfire tracing (`helpers/telemetry.py`), and routes to Gemini vs Ollama based on whether `model_name` is in the configured `gemini_models` list.

New code that needs structured/typed LLM output or tracing should go through `helpers/llm.get_agent`/`run_model`; low-level option plumbing changes belong in `helpers/llm_helper.py` / `helpers/ollama_helper.py`.

### Resume pipeline (`resume/`)

Master Resume lives as markdown parts (`header.md` / `body.md` / `footer.md`, paths from config) combined into one file, then tailored per job description:

1. `resume/tools/process_resume.py` — `--check` validates markdown structure, `--fix` auto-corrects it.
2. `resume/tools/prepare_resume.py` — builds the LLM tailoring prompt (`--llm-prompt`) or assembles a tailored Resume from a folder under `resume/tmp/`.
3. `resume/tools/md2pdf.py` — markdown → PDF via `pandoc`.
4. `resume/tools/compose_resume.py` / `compose_jobs_from_csv.py` — end-to-end automated composition for one job or a whole CSV of jobs (supports `--feedback` loop, see `feedback_loop.py`).
5. `md/` package (formerly `md_tools` — renamed, some docs/comments may still say `md_tools`) — Pydantic models (`models.py`) for Resume sections (Header, WorkExperience, Skills, etc.) with `to_string()`/`from_string()` round-tripping, plus `parse.py`/`format.py` and the `cli.py` validator entrypoint.

The `resume/justfile` `run` recipe shells out to the sibling Rust tool's compiled binary (`tools/prep_for_cv_tail/target/debug/prep_for_tail[_ui]`) — that binary must be built first (`cd ../prep_for_cv_tail && cargo build`).

### Job finder (`job_finder/`)

- `scraper/` — Selenium/`easelenium`-based scrapers per site (`indeed.py`, `linkedin.py`, `stepstone.py`), sharing browser lifecycle and retry logic in `base.py`, with disk caching (`utils/caching_utils.py`) keyed by content hash to avoid re-scraping.
- `reviewer/` — sends each scraped JD plus the candidate's Resume text (`job_finder/data/private/cv.txt`) through an LLM (`reviewer/llm.py`) to get a match percentage and pass/fail (`reviewer/match.py`).
- `cli/` — `fetch_and_match.py` (full scrape+match run), `check_jd.py` (single JD from stdin), `llm_review.py` (re-review an existing CSV/ODF of results).
- Credentials for scrapers come from environment variables via `utils/env_utils.get_credentials(prefix)`, expecting `EMAIL` and `<PREFIX>_PASSWORD` — set in `private/.env` (dotenv-loaded by the justfiles, gitignored).

### Evaluation (`tailor_resume_eval/`)

Compares Resume/JD-matching outputs across 7 independent evaluation engines (DeepEval, Promptfoo, LlamaIndex, Ragas, TruLens, Giskard, TextGrad) under `tools/models_cmp/<engine>/`, each with its own `justfile`. All share `config.yaml` for model lists and job/ground-truth definitions. `tools/eval_performance/` and `tools/parameter_eval/` separately benchmark raw model speed and generation-parameter tuning (temperature/top_p/repeat_penalty) rather than output quality.

### Observability

`helpers/telemetry.py` wires up OpenTelemetry + Logfire + Arize Phoenix instrumentation for LLM agent calls (spans emitted from `helpers/llm/__init__.py:run_agent`). Phoenix UI: `just arize-phoenix` (serves locally; telemetry export no-ops if the collector endpoint isn't reachable).

## Notes

- `pyproject.toml`'s `[tool.pytest.ini_options] pythonpath` includes machine-local paths outside this repo (`/home/kirill/prj/gl/playground`, `/home/kirill/prj/gh/easelenium`) — these are this developer's local checkouts, not general repo dependencies.
- Ruff is configured with `select = ["ALL"]` in both `pyproject.toml` and `ruff.toml` (the latter targets `py313`); test files (`*_test.py`, `test_*.py`) get relaxed rules (no docstrings/annotations/asserts-are-fine).

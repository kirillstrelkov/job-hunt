# ==================== DEFAULT & CLI RUNNER ====================

default:
    @just --list

# Forward any arguments directly to job-hunt CLI dispatcher
# Example: `just run resume template list`
# Example: `just run eval benchmark perf`
run *args:
    uv run job-hunt {{args}}

# ==================== WORKSPACE & DEV ====================

# Install dependencies and package in editable mode
install:
    uv sync
    uv pip install -e .

# Run fast unit test suite
test:
    uv run pytest tests/unit

# Run browser & live LLM integration test suite
test-integration:
    uv run pytest tests/integration

# Code quality check and auto-formatting
lint:
    uv run ruff check src tests
    uv run ruff format src tests

# Clean temporary files, build artifacts, and test caches
clean:
    rm -rf workspace/outputs/* tmp/ .pytest_cache/ .ruff_cache/ logs/

# ==================== RESUME SUBCOMMANDS ====================

# Validate Markdown Resume formatting and structure
resume-check file:
    uv run job-hunt resume check "{{ file }}"

# Check Resume PDF page count and visual fill
resume-check-pdf pdf:
    uv run job-hunt resume check-pdf "{{ pdf }}"

# Tailor master Resume body against a job description
resume-tailor resume jd output="" model="gemma4:e2b":
    uv run job-hunt resume tailor -r "{{ resume }}" -j "{{ jd }}" {{ if output == "" { "" } else { "-o " + output } }} -m "{{ model }}"

# Convert Markdown Resume to PDF via Pandoc / Typst
resume-render input output="":
    uv run job-hunt resume render "{{ input }}" {{ if output == "" { "" } else { "-o " + output } }}

# Auto-correct Markdown syntax errors
resume-fix input output="":
    uv run job-hunt resume fix "{{ input }}" {{ if output == "" { "" } else { "-o " + output } }}

# Combine header, body and footer markdown files into a single Resume
resume-combine header body footer output="":
    uv run job-hunt resume combine -H "{{ header }}" -b "{{ body }}" -f "{{ footer }}" {{ if output == "" { "" } else { "-o " + output } }}

# Substitute header and footer sections in resume markdown file(s)
resume-substitute src output header footer:
    uv run job-hunt resume substitute "{{ src }}" "{{ output }}" --header "{{ header }}" --footer "{{ footer }}"

# Build Resume PDFs from all *_resume.md files in a folder
resume-build-pdfs folder:
    uv run job-hunt resume build-pdfs "{{ folder }}"

# Auto-compose Resume for a target folder
resume-compose folder model="gemma-4-26b-a4b-it":
    uv run job-hunt resume compose "{{ folder }}" --model "{{ model }}"

# Batch compose Resumes from a CSV job list
resume-compose-from-csv csv_path output_folder="workspace/outputs" model="" force="false" feedback="false":
    uv run job-hunt resume compose-from-csv -p "{{ csv_path }}" -f "{{ output_folder }}" {{ if model == "" { "" } else { "-m " + model } }} {{ if force == "true" { "--force" } else { "" } }} {{ if feedback == "true" { "--feedback" } else { "" } }}

# Scaffold workspace directories, jd.txt, and prompt.md from CSV/ODS job matches
resume-scaffold csv_path min_score="80" output_folder="tmp/manual_jds" force="false":
    uv run job-hunt resume scaffold "{{ csv_path }}" --min-score "{{ min_score }}" --folder "{{ output_folder }}" {{ if force == "true" { "--force" } else { "" } }}

# List available resume templates
resume-template-list:
    uv run job-hunt resume template list

# Display a template content
resume-template-show kind="header":
    uv run job-hunt resume template show "{{ kind }}"

# Generate a template scaffold
resume-template-generate name="custom" out="data/templates":
    uv run job-hunt resume template generate -n "{{ name }}" -o "{{ out }}"

# ==================== FINDER SUBCOMMANDS ====================

# Scrape job boards and filter listings with LLM matching
finder-fetch:
    uv run job-hunt finder fetch --log-level debug

# Analyze a single job description file
finder-check-jd jd:
    uv run job-hunt finder check-jd "{{ jd }}"

# Review role match for a single job description file
finder-review jd:
    uv run job-hunt finder review -j "{{ jd }}"

# Re-review matched jobs from CSV or ODF result file
finder-review-csv path:
    uv run job-hunt finder review-csv -p "{{ path }}"

# ==================== CONFIG SUBCOMMANDS ====================

# Display current workspace configuration
config-show:
    uv run job-hunt config show

# Validate configured paths
config-check:
    uv run job-hunt config check

# ==================== UI SUBCOMMANDS ====================

# Launch Streamlit web composer interface
ui:
    uv run job-hunt ui

# ==================== EVAL SUBCOMMANDS ====================

# Run model generation parameter evaluation
eval-params:
    uv run job-hunt eval benchmark params

# Benchmark model inference speed and throughput
eval-perf model="":
    uv run job-hunt eval benchmark perf {{ if model == "" { "" } else { "-m " + model } }}

# Benchmark speed across all configured models
eval-perf-all:
    uv run job-hunt eval benchmark perf-all

# Run Promptfoo prompt quality evaluation
eval-prompts:
    uv run job-hunt eval prompts

# View Promptfoo web dashboard
eval-view:
    uv run job-hunt eval view

# ==================== OLLAMA MODEL BUILDS ====================

# Build custom high-context Ollama model manifests
models-build:
    ollama create gemma4:e2b-ctx65k -f ./src/job_hunt/core/llm/models/gemma4_e2b_ctx65k
    ollama create gemma4:e2b-it-qat-ctx65k -f ./src/job_hunt/core/llm/models/gemma4_e2b_it_ctx65k
    ollama create gemma4:e4b-it-qat-ctx65k -f ./src/job_hunt/core/llm/models/gemma4_e4b_it_ctx65k

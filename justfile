# Root justfile recipes for job-hunt workspace

default:
    @just --list

# Flexible CLI runner: passes any arguments to main CLI entrypoint
# Example: `just run resume check ~/cv.md`
# Example: `just run finder fetch`
# Example: `just run ui`
run *args:
    uv run job-hunt {{args}}

install:
    uv sync
    uv pip install -e .

test:
    uv run pytest tests/unit

test-integration:
    uv run pytest tests/integration

ui:
    uv run job-hunt ui

lint:
    uv run ruff check src tests
    uv run ruff format src tests

"""Typer CLI subcommands for job scraping and matching."""

from pathlib import Path

import typer

finder_app = typer.Typer(
    name="finder",
    help="Job finder operations: fetch listings, review single JD, re-evaluate CSVs",
    add_completion=False,
)


@finder_app.command("fetch")
def finder_fetch(
    log_level: str = typer.Option("INFO", "--log-level", help="Logging level (e.g. DEBUG, INFO, WARNING)"),
):
    """Scrape configured job boards and save listings."""
    typer.echo("Starting job scrapers...")
    from job_hunt.job_finder.cli.fetch_and_match import main as fetch_main

    fetch_main(log_level=log_level.upper())


@finder_app.command("review")
def finder_review(
    jd: Path = typer.Option(..., "--jd", "-j", help="Path to Job Description text"),
):
    """Review role match for a single job description."""
    if not jd.exists():
        typer.secho(f"Error: File not found: {jd}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    from job_hunt.job_finder.reviewer.llm import review_job

    jd_content = jd.read_text(encoding="utf-8")
    score = review_job(jd_content)
    typer.echo(f"Match Score: {score}")


@finder_app.command("review-csv")
def finder_review_csv(
    path: Path = typer.Option(..., "--path", "-p", help="Path to CSV or ODF result file"),
):
    """Re-review matched jobs from a CSV or ODF file."""
    if not path.exists():
        typer.secho(f"Error: File not found: {path}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    from job_hunt.job_finder.cli.llm_review import main as review_csv_main

    review_csv_main(path)

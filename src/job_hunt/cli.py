"""Main CLI application dispatcher for job-hunt."""

import subprocess
import sys
from pathlib import Path

import typer

app = typer.Typer(
    name="job-hunt",
    help="Job Hunt & Resume Tailoring Workspace CLI",
    add_completion=False,
)

resume_app = typer.Typer(help="Resume operations: check, tailor, fix, render")
finder_app = typer.Typer(help="Job finder operations: fetch listings, match JD")
eval_app = typer.Typer(help="Evaluation & benchmarking framework")

app.add_typer(resume_app, name="resume")
app.add_typer(finder_app, name="finder")
app.add_typer(eval_app, name="eval")


@resume_app.command("check")
def resume_check(
    file_path: Path = typer.Argument(..., help="Path to Markdown Resume file"),
) -> None:
    """Validate Markdown Resume formatting and structure against schema."""
    from job_hunt.resume.parse import split_markdown_into_sections

    if not file_path.exists():
        typer.secho(f"Error: File not found: {file_path}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    content = file_path.read_text(encoding="utf-8")
    try:
        sections = split_markdown_into_sections(content, filepath=file_path)
        typer.secho(f" Valid Markdown Resume: {file_path.name}", fg=typer.colors.GREEN)
        typer.echo(f"  Sections found: {len(sections)}")
    except Exception as e:
        typer.secho(f" Validation failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)


@resume_app.command("tailor")
def resume_tailor(
    resume: Path = typer.Option(..., "--resume", "-r", help="Path to Master Resume body markdown"),
    jd: Path = typer.Option(..., "--jd", "-j", help="Path to Job Description file"),
    output: Path = typer.Option(Path("tailored_resume.md"), "--output", "-o", help="Path for output Markdown/PDF"),
    model: str = typer.Option("gemma4:e2b", "--model", "-m", help="LLM model name to use"),
) -> None:
    """Tailor a master Resume body against a specific job description."""
    from job_hunt.config.config import DEFAULT_CONFIG
    from job_hunt.core.llm import run_model

    if not resume.exists():
        typer.secho(f"Error: Resume file not found: {resume}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    if not jd.exists():
        typer.secho(f"Error: Job description file not found: {jd}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    prompt_path = DEFAULT_CONFIG.tailor.prompt
    if not prompt_path.exists():
        typer.secho(f"Error: Tailoring prompt missing: {prompt_path}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    resume_text = resume.read_text(encoding="utf-8")
    jd_text = jd.read_text(encoding="utf-8")
    template = prompt_path.read_text(encoding="utf-8")

    full_prompt = template.format(resume=resume_text, cv=resume_text, job_description=jd_text)

    typer.echo(f"Tailoring Resume with model '{model}'...")
    result = run_model(model_name=model, prompt=full_prompt)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result, encoding="utf-8")
    typer.secho(f" Tailored Resume saved to {output.resolve()}", fg=typer.colors.GREEN)


@resume_app.command("render")
def resume_render(
    input_file: Path = typer.Argument(..., help="Path to Markdown Resume file"),
    output_pdf: Path = typer.Option(None, "--output", "-o", help="Path to target PDF file"),
) -> None:
    """Convert Markdown Resume to PDF via pandoc/typst."""
    if not input_file.exists():
        typer.secho(f"Error: File not found: {input_file}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    out_path = output_pdf or input_file.with_suffix(".pdf")
    cmd = ["pandoc", str(input_file), "-o", str(out_path)]
    try:
        subprocess.run(cmd, check=True)
        typer.secho(f" Rendered PDF saved to {out_path.resolve()}", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f" PDF rendering failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)


@finder_app.command("fetch")
def finder_fetch() -> None:
    """Scrape configured job boards and save listings."""
    typer.echo("Starting job scrapers...")
    from job_hunt.job_finder.cli.fetch_and_match import main as fetch_main

    fetch_main()


@finder_app.command("review")
def finder_review(
    jd: Path = typer.Option(..., "--jd", "-j", help="Path to Job Description text"),
) -> None:
    """Review role match for a single job description."""
    if not jd.exists():
        typer.secho(f"Error: File not found: {jd}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    from job_hunt.job_finder.reviewer.llm import review_job

    jd_content = jd.read_text(encoding="utf-8")
    score = review_job(jd_content)
    typer.echo(f"Match Score: {score}")


@app.command("ui")
def launch_ui() -> None:
    """Launch the Streamlit web composer interface."""
    app_path = Path(__file__).parent / "ui" / "app.py"
    typer.echo(f"Launching Streamlit app at {app_path}...")
    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path)]
    subprocess.run(cmd)


if __name__ == "__main__":
    app()

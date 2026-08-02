"""Typer CLI subcommands for Resume management and template operations."""

import subprocess
from pathlib import Path

import typer

resume_app = typer.Typer(
    name="resume",
    help="Resume operations: check, tailor, fix, render, compose, and templates",
    add_completion=False,
)

template_app = typer.Typer(
    name="template",
    help="Template sub-subcommands: list, show, generate",
    add_completion=False,
)

resume_app.add_typer(template_app, name="template")


@resume_app.command("check")
def resume_check(
    file_path: Path = typer.Argument(..., help="Path to Markdown Resume file"),
):
    """Validate Markdown Resume formatting and structure against schema."""
    from job_hunt.resume.parse import split_markdown_into_sections

    if not file_path.exists():
        typer.secho(f"Error: File not found: {file_path}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    content = file_path.read_text(encoding="utf-8")
    try:
        sections = split_markdown_into_sections(content, filepath=file_path)
        typer.secho(f"Valid Markdown Resume: {file_path.name}", fg=typer.colors.GREEN)
        typer.echo(f"  Sections found: {len(sections)}")
    except Exception as e:
        typer.secho(f"Validation failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)


@resume_app.command("tailor")
def resume_tailor(
    resume: Path = typer.Option(None, "--resume", "-r", help="Path to Master Resume body markdown"),
    jd: Path = typer.Option(None, "--jd", "-j", help="Path to Job Description file"),
    title: str = typer.Option(None, "--title", "-t", help="Job title string (alternative to --jd)"),
    output: Path = typer.Option(Path("tailored_resume.md"), "--output", "-o", help="Path for output markdown file"),
    model: str = typer.Option(None, "--model", "-m", help="LLM model name to use"),
    force: bool = typer.Option(False, "--force", help="Overwrite output even if it already exists"),
):
    """Tailor a master Resume body against a job description or job title using an LLM."""
    from job_hunt.core.ollama_helper import get_eval_model
    from job_hunt.resume.prepare_llm_prompt import tailor_for_description, tailor_for_title
    from job_hunt.resume.tailor_resume_body import process_output_of_ollama, run_ollama

    if not resume:
        typer.secho("Error: --resume is required", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    if not jd and not title:
        typer.secho("Error: either --jd or --title is required", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    if not resume.exists():
        typer.secho(f"Error: Resume file not found: {resume}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    if output.exists() and not force:
        typer.secho(f"Output already exists (use --force to overwrite): {output}", fg=typer.colors.YELLOW)
        return

    import tempfile

    resolved_model = model or get_eval_model()

    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
        tmp_prompt_path = Path(tmp.name)

    # Note: prepare_llm_prompt.py relies on MASTERCV_PATH env var.
    if title:
        tailor_for_title(str(tmp_prompt_path), title)
    else:
        if not jd.exists():
            typer.secho(f"Error: Job description file not found: {jd}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
        tailor_for_description(str(tmp_prompt_path), str(jd))

    typer.echo(f"Tailoring Resume with model '{resolved_model}'...")
    prompt_content = tmp_prompt_path.read_text(encoding="utf-8")
    result = run_ollama(prompt_content, resolved_model)
    process_output_of_ollama(result, output)
    typer.secho(f"Tailored Resume saved to {output.resolve()}", fg=typer.colors.GREEN)


@resume_app.command("render")
def resume_render(
    input_file: Path = typer.Argument(..., help="Path to Markdown Resume file"),
    output_pdf: Path = typer.Option(None, "--output", "-o", help="Path to target PDF file"),
):
    """Convert Markdown Resume to PDF via pandoc/typst."""
    if not input_file.exists():
        typer.secho(f"Error: File not found: {input_file}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    out_path = output_pdf or input_file.with_suffix(".pdf")
    cmd = ["pandoc", str(input_file), "-o", str(out_path)]
    try:
        subprocess.run(cmd, check=True)
        typer.secho(f"Rendered PDF saved to {out_path.resolve()}", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"PDF rendering failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)


@resume_app.command("fix")
def resume_fix(
    input_file: Path = typer.Argument(..., help="Path to Markdown Resume file"),
    output_file: Path = typer.Option(None, "--output", "-o", help="Output fixed Markdown file"),
):
    """Auto-correct Markdown Resume syntax and formatting errors."""
    from job_hunt.resume.parse import split_markdown_into_sections
    from job_hunt.resume.process_resume import fix_markdown

    if not input_file.exists():
        typer.secho(f"Error: File not found: {input_file}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    raw_text = input_file.read_text(encoding="utf-8")
    sections = split_markdown_into_sections(raw_text, filepath=input_file)
    fixed_text = fix_markdown(sections)

    target_path = output_file or input_file
    target_path.write_text(fixed_text, encoding="utf-8")
    typer.secho(f"Fixed Resume saved to {target_path.resolve()}", fg=typer.colors.GREEN)


@resume_app.command("compose")
def resume_compose(
    folder: Path = typer.Argument(..., help="Folder containing job inputs & config"),
    model: str = typer.Option("gemma-4-26b-a4b-it", "--model", "-m", help="LLM model name to use"),
):
    """Auto-compose Resume for a target folder."""
    from job_hunt.resume.compose_resume import compose_resume

    if not folder.exists():
        typer.secho(f"Error: Folder not found: {folder}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    compose_resume(folder, model=model)
    typer.secho(f"Composed Resume for folder {folder}", fg=typer.colors.GREEN)


@resume_app.command("compose-csv")
def resume_compose_csv(
    csv_path: Path = typer.Option(..., "--path", "-p", help="Path to jobs CSV file"),
    folder: Path = typer.Option(Path("workspace/outputs"), "--folder", "-f", help="Output target directory"),
):
    """Batch compose Resumes from a CSV job list."""
    from job_hunt.resume.compose_jobs_from_csv import main as compose_csv_main

    if not csv_path.exists():
        typer.secho(f"Error: CSV file not found: {csv_path}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    compose_csv_main(path=csv_path, folder=folder)
    typer.secho("Batch CSV composition complete.", fg=typer.colors.GREEN)


@resume_app.command("combine")
def resume_combine(
    header: Path = typer.Option(..., "--header", "-H", help="Path to header markdown file"),
    body: Path = typer.Option(..., "--body", "-b", help="Path to body markdown file"),
    footer: Path = typer.Option(..., "--footer", "-f", help="Path to footer markdown file"),
    output: Path = typer.Option(None, "--output", "-o", help="Output path; prints to stdout if omitted"),
):
    """Combine header, body and footer markdown files into a single Resume document."""
    from job_hunt.resume.combine_resume_parts import combine_resume_part_files

    for p in (header, body, footer):
        if not p.exists():
            typer.secho(f"Error: File not found: {p}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)

    combined = combine_resume_part_files(header, body, footer)
    if output:
        output.write_text(combined, encoding="utf-8")
        typer.secho(f"Combined Resume saved to {output.resolve()}", fg=typer.colors.GREEN)
    else:
        typer.echo(combined)


@resume_app.command("check-pdf")
def resume_check_pdf(
    pdf: Path = typer.Argument(..., help="Path to the PDF file to check"),
):
    """Check Resume PDF page count and visual fill."""
    from job_hunt.resume.check_pdf import check_pdf

    if not pdf.exists():
        typer.secho(f"Error: File not found: {pdf}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    errors = check_pdf(pdf)
    if errors:
        for err in errors:
            typer.secho(err, fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    typer.secho(f"PDF OK: {pdf}", fg=typer.colors.GREEN)


@resume_app.command("build-pdfs")
def resume_build_pdfs(
    folder: Path = typer.Argument(..., help="Folder containing *_resume.md files"),
):
    """Build Resume PDFs from all *_resume.md files in a folder."""
    from job_hunt.resume.create_resume_from_titles import main as build_pdfs_main

    if not folder.exists():
        typer.secho(f"Error: Folder not found: {folder}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    build_pdfs_main(folder)


@resume_app.command("filter")
def resume_filter(
    input_path: Path = typer.Argument(..., help="Input directory or markdown file path"),
    output_path: Path = typer.Argument(..., help="Output directory or file path"),
    header: Path = typer.Option(..., "--header", help="Path to header markdown file"),
    footer: Path = typer.Option(..., "--footer", help="Path to footer markdown file"),
):
    """Scan markdown file(s), filter for full resumes, and replace header/footer sections."""
    from job_hunt.resume.filter_and_replace_resume import main as filter_main

    filter_main(src=input_path, output=output_path, header=header, footer=footer)
    typer.secho("Filtering complete.", fg=typer.colors.GREEN)


# --- Level 3 Commands: job-hunt resume template ... ---


@template_app.command("list")
def template_list():
    """List available header, footer, and tailoring prompt templates."""
    from job_hunt.config.config import DEFAULT_CONFIG

    typer.echo("Configured Templates:")
    typer.echo(f"  Header: {DEFAULT_CONFIG.composer.header}")
    typer.echo(f"  Body:   {DEFAULT_CONFIG.composer.body}")
    typer.echo(f"  Footer: {DEFAULT_CONFIG.composer.footer}")
    typer.echo(f"  Prompt: {DEFAULT_CONFIG.tailor.prompt}")


@template_app.command("show")
def template_show(
    kind: str = typer.Argument("header", help="Template type: header, body, footer, prompt"),
):
    """Display the contents of a template."""
    from job_hunt.config.config import DEFAULT_CONFIG

    mapping = {
        "header": DEFAULT_CONFIG.composer.header,
        "body": DEFAULT_CONFIG.composer.body,
        "footer": DEFAULT_CONFIG.composer.footer,
        "prompt": DEFAULT_CONFIG.tailor.prompt,
    }

    path = mapping.get(kind.lower())
    if not path or not path.exists():
        typer.secho(f"Error: Template '{kind}' not found at {path}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    typer.echo(f"--- Template: {kind} ({path}) ---")
    typer.echo(path.read_text(encoding="utf-8"))


@template_app.command("generate")
def template_generate(
    name: str = typer.Option("custom_template", "--name", "-n", help="Template scaffold name"),
    output_dir: Path = typer.Option(Path("data/templates"), "--out", "-o", help="Target directory"),
):
    """Generate a new Resume template scaffold."""
    output_dir.mkdir(parents=True, exist_ok=True)
    header_file = output_dir / f"{name}_header.md"
    body_file = output_dir / f"{name}_body.md"
    footer_file = output_dir / f"{name}_footer.md"

    header_file.write_text("# Candidate Name\n\nCity, Country | email@example.com | +00 123456\n\n---\n")
    body_file.write_text("## Summary\n\nProfessional summary...\n\n## Experience\n\nJob details...\n")
    footer_file.write_text("## Education\n\nDegree details...\n")

    typer.secho(f"Generated template scaffold '{name}' in {output_dir.resolve()}", fg=typer.colors.GREEN)

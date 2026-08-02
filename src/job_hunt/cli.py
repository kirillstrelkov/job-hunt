"""Main hierarchical CLI application dispatcher for job-hunt."""

import subprocess
import sys
from pathlib import Path

import typer

from job_hunt.config.cli import config_app
from job_hunt.eval.cli import eval_app
from job_hunt.job_finder.cli import finder_app
from job_hunt.resume.cli import resume_app

app = typer.Typer(
    name="job-hunt",
    help="Job Hunt & Resume Workspace Multi-Level CLI",
    add_completion=False,
)

# Register Level 2 sub-apps
app.add_typer(resume_app, name="resume")
app.add_typer(finder_app, name="finder")
app.add_typer(eval_app, name="eval")
app.add_typer(config_app, name="config")


@app.command("ui")
def launch_ui():
    """Launch the Streamlit web composer interface."""
    app_path = Path(__file__).parent / "ui" / "app.py"
    typer.echo(f"Launching Streamlit app at {app_path}...")
    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path)]
    subprocess.run(cmd)


if __name__ == "__main__":
    app()

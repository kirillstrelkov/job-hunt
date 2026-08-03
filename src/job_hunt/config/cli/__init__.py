"""Typer CLI subcommands for configuration management."""

from pathlib import Path

import typer

config_app = typer.Typer(
    name="config",
    help="Workspace configuration operations: show, check, generate",
    add_completion=False,
)


@config_app.command("show")
def config_show():
    """Display current resolved workspace configuration."""
    from job_hunt.config.config import DEFAULT_CONFIG

    typer.echo(f"Configuration file: {DEFAULT_CONFIG.get_path()}")
    typer.echo(f"Root path: {DEFAULT_CONFIG.get_root_path()}")
    typer.echo(f"Temporary output directory: {DEFAULT_CONFIG.get_tmp_root_output_dir()}")
    typer.echo(f"Default Eval Model: {DEFAULT_CONFIG.llm.eval_model}")
    typer.echo(f"Default Fix Model: {DEFAULT_CONFIG.llm.fix_model}")


@config_app.command("check")
def config_check(
    config_path: Path = typer.Argument(
        None, help="Path to config.yaml to validate (defaults to the workspace config.yaml)"
    ),
):
    """Validate that all paths referenced in the config file exist."""
    from job_hunt.config.config import DEFAULT_CONFIG, check_config

    target = config_path if config_path is not None else DEFAULT_CONFIG.get_path()
    success = check_config(target)
    if success:
        typer.secho(f"Configuration validation successful: All paths exist. ({target})", fg=typer.colors.GREEN)
    else:
        typer.secho(
            f"Configuration validation failed: Some paths are missing. ({target})", fg=typer.colors.RED, err=True
        )
        raise typer.Exit(code=1)


@config_app.command("generate")
def config_generate(
    out_path: Path = typer.Option(
        Path("src/job_hunt/config/config.yaml"), "--out", "-o", help="Target output YAML path"
    ),
):
    """Generate default config.yaml file."""
    from job_hunt.config.config import create_default_config

    create_default_config(out_path)
    typer.secho(f"Generated default config at {out_path.resolve()}", fg=typer.colors.GREEN)

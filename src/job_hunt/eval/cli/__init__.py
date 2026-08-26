"""Typer CLI subcommands for evaluation and benchmarking."""

import subprocess

import typer

eval_app = typer.Typer(
    name="eval",
    help="Evaluation and benchmarking operations",
    add_completion=False,
)

benchmark_app = typer.Typer(
    name="benchmark",
    help="Benchmark sub-subcommands: params, perf, perf-all",
    add_completion=False,
)

eval_app.add_typer(benchmark_app, name="benchmark")


@eval_app.command("prompts")
def eval_prompts():
    """Run Promptfoo prompt quality evaluation."""
    from job_hunt.eval.tools.eval_quality_with_gt.run import main as eval_quality_main

    eval_quality_main()


@eval_app.command("view")
def eval_view():
    """Launch Promptfoo web dashboard."""
    from job_hunt.core.binary_helper import get_npx

    cmd = [get_npx(), "-y", "promptfoo@latest", "view"]
    subprocess.run(cmd)


# --- Level 3 Commands: job-hunt eval benchmark ... ---


@benchmark_app.command("params")
def benchmark_params():
    """Run model generation parameter evaluation (temperature, top_p, repeat_penalty)."""
    from job_hunt.eval.tools.parameter_eval.run import main as eval_params_main

    eval_params_main()


@benchmark_app.command("perf")
def benchmark_perf(
    model: str = typer.Option("", "--model", "-m", help="Specific LLM model to benchmark"),
):
    """Benchmark model inference latency and throughput."""
    from job_hunt.eval.tools.eval_performance.run_single_model import main as perf_single_main

    perf_single_main()


@benchmark_app.command("perf-all")
def benchmark_perf_all():
    """Benchmark speed and throughput across all configured models."""
    from job_hunt.eval.tools.eval_performance.run_all_models import main as perf_all_main

    perf_all_main()

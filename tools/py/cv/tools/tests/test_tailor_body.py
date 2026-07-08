from pathlib import Path

import pytest
from cv.tools.tailor_body import run_ollama

from helpers.tmp_helper import get_tmp_folder


def prepare_llm_prompt_file(test_file_path: str | Path) -> str:
    """Prepare prompt data by combining example files, format with template, and save to a test prompt file. Returns prompt content."""
    current_file = Path(test_file_path).resolve()
    project_root = current_file.parent
    while project_root != project_root.parent:
        if (project_root / "pyproject.toml").exists():
            break
        project_root = project_root.parent

    # Define paths
    template_path = project_root / "cv" / "prompts" / "tailor_for_description.md"
    header_path = project_root / "cv" / "example" / "header.md"
    body_path = project_root / "cv" / "example" / "body.md"
    footer_path = project_root / "cv" / "example" / "footer.md"
    jd_path = project_root / "job_finder" / "data" / "test" / "tesla_go.txt"

    # Combine CV files
    header_content = header_path.read_text(encoding="utf-8")
    body_content = body_path.read_text(encoding="utf-8")
    footer_content = footer_path.read_text(encoding="utf-8")
    combined_cv = f"{header_content}\n\n{body_content}\n\n{footer_content}"

    # Read JD and template
    jd_content = jd_path.read_text(encoding="utf-8")
    prompt_template = template_path.read_text(encoding="utf-8")

    # Format the prompt
    prompt_content = prompt_template.format(
        master_cv=combined_cv,
        job_description=jd_content,
    )

    # Save to temp folder as llm_prompt_test.txt
    tmp_dir = get_tmp_folder(test_file_path)
    prompt_test_file = tmp_dir / "llm_prompt_test.txt"
    prompt_test_file.write_text(prompt_content, encoding="utf-8")
    return prompt_content


@pytest.mark.parametrize(
    "model",
    [
        "gemini-3.1-flash-lite",
        "gemma4:e2b-ctx16k",
    ],
)
def test_run_ollama(model):
    """Test that run_ollama runs correctly using prompt generated from combined example CV and tesla_go JD."""
    prompt_content = prepare_llm_prompt_file(__file__)

    # Run Ollama inference
    result = run_ollama(prompt_content, model)

    assert result["model"] == model
    assert isinstance(result["response"], str)
    assert len(result["response"]) > 500
    assert result["total_time"] >= 0.0

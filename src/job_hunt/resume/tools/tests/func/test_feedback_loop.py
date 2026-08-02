import pytest

from job_hunt.resume.feedback_loop import fix_with_feedback
from job_hunt.resume.process_resume import check_markdown


@pytest.mark.parametrize(
    "model",
    [
        "gemma4:e4b-it-qat-ctx65k",  # default fix model from job_hunt.config.yaml
        # "gemma4:e2b-ctx65k", doesn't work
        # "gemma4:e2b-it-qat-ctx65k", Performs worse then others
    ],
)
def test_fix_with_feedback_real_gemma(model: str):
    md = """# John Doe

Berlin, Germany | <john.doe@example.com> | +49 123 4567890  
[linkedin.com/in/johndoe](https://www.linkedin.com/in/johndoe/) | [github.com/johndoe](https://github.com/johndoe)

## Summary

Software Engineer with extensive experience.

## Skills

**Languages**: Python, Go, C++
**Databases**: PostgreSQL

## Work experience

**Software Engineer** | _Tech Corp_ | Jan 2024 - Present

- Designed high throughput APIs.
- Mentored junior engineers.
- Skills: Python, Go

## Personal projects

**[Project A](https://github.com/a)** | Jan 2023 - Present

- Built a custom tool.

\\break

## Courses and certificates

- Course A | _Provider_ \\hfill Jan 2023

## Education

**Bachelor of Science** | _University_ | January 2020 - December 2024

## Languages

**English**: Native
"""
    res = fix_with_feedback(md, model)

    assert isinstance(res, str)
    assert len(res) > 200

    errors = check_markdown(res)
    errros_str = "\n".join([str(e) for e in errors])
    assert not errors, f"Fixed markdown still has {len(errors)} errors:\n{errros_str}\n\nFixed MD:\n{res}"

    assert "## Error" not in res
    assert "```" not in res
    assert "\\break" in res

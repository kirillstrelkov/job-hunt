import pytest

from cv.tools.feedback_loop import fix_with_feedback
from cv.tools.process_cv import check_markdown


@pytest.mark.parametrize(
    "model",
    [
        "gemma4:e2b-ctx65k",
        # "gemma4:e2b-it-qat-ctx65k", Performs worse then others
        "gemma4:e4b-it-qat-ctx65k",
    ],
)
def test_fix_with_feedback_real_gemma(model: str):
    md = """# John Doe

Berlin, Germany | <john.doe@example.com> | +49 123 4567890\\
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
    assert not errors, f"Fixed markdown still has errors: {errors}\n\nFixed MD:\n{res}"

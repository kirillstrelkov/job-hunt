from cv.tools.process_cv import fix_markdown
from md.format import format


def test_format_courses_equivalence() -> None:
    md = r"""## Courses and certificates

- Agentic AI Nanodegree | _Udacity_ \hfill Jul 2026
"""
    res = format(md)
    assert res == md


def test_do_fix_sorting_courses() -> None:
    md = """## Courses and certificates

- Old Course | _Institution_ | Jan 2020
- Recent Course | _Institution_ | Jul 2026
- Mid Course | _Institution_ | Feb 2023
"""
    res = fix_markdown(md)
    expected_order = [
        "Recent Course",
        "Mid Course",
        "Old Course",
    ]
    # Check that they appear in the correct order in the formatted output
    positions = [res.find(course) for course in expected_order]
    assert all(pos != -1 for pos in positions)
    assert positions == sorted(positions)


def test_do_fix_sorting_personal_projects() -> None:
    md = """## Personal projects

**[Old Project](https://github.com/old)** | Jan 2020

- Old project description
- Skills: Python

**[Recent Project](https://github.com/recent)** | Jul 2026

- Recent project description
- Skills: Go

**[Mid Project](https://github.com/mid)** | Feb 2023

- Mid project description
- Skills: Java
"""
    res = fix_markdown(md)
    expected_order = [
        "Recent Project",
        "Mid Project",
        "Old Project",
    ]
    positions = [res.find(project) for project in expected_order]
    assert all(pos != -1 for pos in positions)
    assert positions == sorted(positions)

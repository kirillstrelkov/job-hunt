from pathlib import Path

from cv.tools.checker import get_section_class
from cv.tools.fixer import (
    ChronologicalSortingFix,
    MonthShortenerFix,
    SkillsFix,
    ThesisFix,
    TrailingDotFix,
    fix_last_pipe,
)
from cv.tools.process_cv import do_fix
from md.models import CV, PersonalProjects
from md.parse import Section, split_markdown_into_sections


def parse_section(text: str) -> Section:
    """Helper to parse a section from a multiline markdown string."""
    text = text.strip()
    sections = split_markdown_into_sections(text, filepath=Path("dummy.md"))
    sec = sections[0]
    sec_class = get_section_class(sec)
    return sec_class.from_string(text, filepath=sec.filepath, indexed_lines=sec.indexed_lines)


def test_skills_fix():
    sec = parse_section("""

## Skills

**Programming Languages:** Python, Go, C++, Java, Ruby, JavaScript, SQL, Bash  
**ML/AI & Scientific Computing:** TensorFlow, NumPy, Pandas, Scikit-learn, PyTorch, LLMs (OpenAI, Gemini), RAG Pipelines  
**Cloud & DevOps:** Docker, Kubernetes, GitHub Actions, CI/CD, Ansible, Prometheus, Grafana, HashiCorp Vault, Terraform, AWS (Foundations)  
**Databases & Storage:** PostgreSQL, MongoDB, Redis, Artifactory  
**Frameworks & Tools:** FastAPI, React, Django, Spring Boot, Git, Jenkins, SLurm, Selenium WebDriver, Bazel, Scikit-learn  

    """)
    sec = SkillsFix().fix(sec)
    # The header line is at index 0, the first content line is at index 1
    assert len(sec.indexed_lines) > 5


def test_thesis_fix():
    sec = parse_section("""
## Work experience
**Developer** | _Company_ | Jan 2024
- Thesis: something
    """)
    # keep_thesis is True by default
    sec = ThesisFix().fix(sec, keep_thesis=True)
    assert len(sec.indexed_lines) == 3

    # keep_thesis is False
    sec = ThesisFix().fix(sec, keep_thesis=False)
    assert len(sec.indexed_lines) == 2
    assert sec.indexed_lines[1].line == "**Developer** | _Company_ | Jan 2024"


def test_month_shortener_fix():
    sec = parse_section("""
## Summary
Working from January 2024 to December 2024
    """)
    sec = MonthShortenerFix().fix(sec)
    assert sec.indexed_lines[1].line == "Working from Jan 2024 to Dec 2024"


def test_trailing_dot_fix():
    sec = parse_section("""
## Work experience
**Developer** | _Company_ | Jan 2024
- Testing software.
- Developing software.   
    """)
    sec = TrailingDotFix().fix(sec)
    assert sec.indexed_lines[2].line == "- Testing software"
    assert sec.indexed_lines[3].line == "- Developing software"


def test_last_pipe_fix():
    md = """
# John Doe

Berlin, Germany | <john.doe@example.com> | +49 123 4567890  
[linkedin.com/in/johndoe](https://www.linkedin.com/in/johndoe/) | [github.com/johndoe](https://github.com/johndoe)

## Work experience
**Tester** | _ASM_ | Jun 2007
    """
    fixed_md = fix_last_pipe(md)
    assert "john.doe@example.com> | +49 123 4567890" in fixed_md
    assert r"_ASM_ \hfill Jun 2007" in fixed_md


def test_chronological_sorting_fix_personal_projects():
    sec = PersonalProjects.from_string(
        """
## Personal projects

**[Proj A](link)** | _Udemy_ | Jul 2024
- Detail A

**[Proj B](link)** | _Udemy_ | Aug 2025
- Detail B
    """,
        Path("fake"),
        [],
    )
    sec = ChronologicalSortingFix().fix(sec)
    new_text = sec.to_string()
    assert new_text.index("Proj B") < new_text.index("Proj A"), f"proj B should be before proj A: {new_text}"


def test_do_fix_cv_integration():
    cv = CV.from_string("""
# John Doe

Berlin, Germany | <john.doe@example.com> | +49 123 4567890  
[linkedin.com/in/johndoe](https://www.linkedin.com/in/johndoe/) | [github.com/johndoe](https://github.com/johndoe)

## Summary
Developer.

## Skills
**Python**: advanced

## Work experience
**Tester** | _ASM_ | Jun 2007

## Education

**Bachelor of Science in Computer Science** | _Technical University of Munich, Germany_ | 2010 - 2014

- Thesis: [Automated web test framework development](https://example.com/thesis.pdf)

## Languages

**English**: Native, **German**: B2 (Upper Intermediate), **Spanish**: A2 (Elementary)

    """)
    fixed_cv = do_fix(cv, keep_thesis=False)
    assert fixed_cv.skills.indexed_lines[1].line == "**Python**: advanced\\"

    cv_str = fixed_cv.to_string()
    assert "Developer." in cv_str
    assert "Thesis" not in cv_str
    assert "**Tester** | _ASM_ | Jun 2007" in cv_str
    assert "john.doe@example.com> | +49 123 4567890" in cv_str

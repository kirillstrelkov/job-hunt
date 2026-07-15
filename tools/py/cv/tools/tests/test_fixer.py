from pathlib import Path

from cv.tools.checker import get_section_class
from cv.tools.fixer import (
    ChronologicalSortingFix,
    CourseCertificateFormatterFix,
    LastPipeFix,
    MonthShortenerFix,
    SkillsFix,
    ThesisFix,
    TrailingDotFix,
)
from cv.tools.process_cv import do_fix
from md_tools.models import CV, CourseOrCertificate, PersonalProjects, Section, SectionConstant
from md_tools.parse import split_markdown_into_sections


def parse_section(text: str) -> Section:
    """Helper to parse a section from a multiline markdown string."""
    text = text.strip()
    sections = split_markdown_into_sections(text, filepath=Path("dummy.md"))
    sec = sections[0]
    sec_class = get_section_class(sec)
    return sec_class.from_string(text, filepath=sec.filepath, raw_lines=sec.raw_lines)


def test_skills_fix():
    sec = parse_section("""
## Skills
**Python**: advanced
**Go**: basic  

    """)
    sec = SkillsFix().fix(sec)
    # The header line is at index 0, the first content line is at index 1
    assert sec.raw_lines[1].raw_line == "**Python**: advanced  "
    assert sec.raw_lines[2].raw_line == "**Go**: basic  "


def test_thesis_fix():
    sec = parse_section("""
## Work experience
**Developer** | Jan 2024
- Thesis: something
    """)
    # keep_thesis is True by default
    sec = ThesisFix().fix(sec, keep_thesis=True)
    assert len(sec.raw_lines) == 3

    # keep_thesis is False
    sec = ThesisFix().fix(sec, keep_thesis=False)
    assert len(sec.raw_lines) == 2
    assert sec.raw_lines[1].raw_line == "**Developer** | Jan 2024"


def test_month_shortener_fix():
    sec = parse_section("""
## Summary
Working from January 2024 to December 2024
    """)
    sec = MonthShortenerFix().fix(sec)
    assert sec.raw_lines[1].raw_line == "Working from Jan 2024 to Dec 2024"


def test_trailing_dot_fix():
    sec = parse_section("""
## Work experience
Developing software.
Developing software.   
    """)
    sec = TrailingDotFix().fix(sec)
    assert sec.raw_lines[1].raw_line == "Developing software"
    assert sec.raw_lines[2].raw_line == "Developing software"


def test_course_certificate_formatter_fix():
    sec = parse_section("""
## Courses and certificates
  Course Name Jul 2026
- Course Name Jul 2026
    """)
    sec = CourseCertificateFormatterFix().fix(sec)
    assert sec.raw_lines[1].raw_line == "- Course Name \\hfill Jul 2026"
    assert sec.raw_lines[2].raw_line == "- Course Name \\hfill Jul 2026"


def test_last_pipe_fix():
    sec = parse_section("""
## Work experience
**Tester** | _ASM_ | Jun 2007
    """)
    sec = LastPipeFix().fix(sec)
    assert sec.raw_lines[1].raw_line == "**Tester** | _ASM_ \\hfill Jun 2007"


def test_chronological_sorting_fix_personal_projects():
    sec = PersonalProjects.from_string(
        """
## Personal projects

**[Proj A](link)** | _Udemy_ \\hfill Jul 2024
- Detail A

**[Proj B](link)** | _Udemy_ \\hfill Aug 2025
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
- Thesis: assembler logic
    """)
    # Run do_fix with keep_thesis=False
    fixed_cv = do_fix(cv, keep_thesis=False)

    # Skills line should end with two spaces
    assert fixed_cv.skills.raw_lines[1].raw_line == "**Python**: advanced  "
    # Thesis line should be removed from work experience
    work_lines = [l.raw_line for l in fixed_cv.body.work_experience_sec.raw_lines]
    assert not any("Thesis" in l for l in work_lines)
    # Last pipe in WorkExperience should be replaced with \hfill
    assert "**Tester** | _ASM_ \\hfill Jun 2007" in work_lines

from pathlib import Path

from cv.tools.checker import (
    ASpaceCheck,
    BraketCheck,
    ChronologicalCheck,
    DotCheck,
    DurationCheck,
    FormatCheck,
    RequiredSectionsCheck,
    TwoSpaceCheck,
    check,
    make_error,
)
from md.models import SectionConstant
from md.parse import Heading, IndexedLine, Section


def test_dot_check():
    sec1 = Section(
        heading=Heading(text=SectionConstant.WORK_EXPERIENCE, heading_prefix="##"),
        filepath=Path("dummy.md"),
        indexed_lines=[
            IndexedLine(line="Senior developer.", index=1),
            IndexedLine(line="Developing software", index=2),
        ],
    )
    checker = DotCheck()
    errors = checker.check(sec1)
    assert len(errors) == 1
    assert errors[0].line_num == 1
    assert "ends with a dot" in errors[0].msg

    sec2 = Section(
        heading=Heading(text=SectionConstant.SUMMARY, heading_prefix="##"),
        filepath=Path("dummy.md"),
        indexed_lines=[IndexedLine(line="Experienced developer.", index=1)],
    )
    assert len(checker.check(sec2)) == 0


def test_two_space_check():
    checker = TwoSpaceCheck()

    sec_skills_err = Section(
        heading=Heading(text=SectionConstant.SKILLS, heading_prefix="##"),
        filepath=Path("dummy.md"),
        indexed_lines=[
            IndexedLine(line="**Python**: advanced", index=1),
            IndexedLine(line="**Go**: basic  ", index=2),
        ],
    )
    errors = checker.check(sec_skills_err)
    assert len(errors) == 1
    assert errors[0].line_num == 1
    assert "must end with exactly two spaces" in errors[0].msg

    sec_other_err = Section(
        heading=Heading(text=SectionConstant.WORK_EXPERIENCE, heading_prefix="##"),
        filepath=Path("dummy.md"),
        indexed_lines=[
            IndexedLine(line="Senior Developer  ", index=1),
            IndexedLine(line="Developing products", index=2),
        ],
    )
    errors = checker.check(sec_other_err)
    assert len(errors) == 1
    assert errors[0].line_num == 1
    assert "ends with two spaces" in errors[0].msg


def test_a_space_check():
    checker = ASpaceCheck()
    sec = Section(
        heading=Heading(text=SectionConstant.SUMMARY, heading_prefix="##"),
        filepath=Path("dummy.md"),
        indexed_lines=[
            IndexedLine(line="This is a test.", index=1),
            IndexedLine(line="This is another test.", index=2),
        ],
    )
    errors = checker.check(sec)
    assert len(errors) == 1
    assert "contains ' a '" in errors[0].msg

    sec_courses = Section(
        heading=Heading(text=SectionConstant.COURSES_AND_CERTIFICATES, heading_prefix="##"),
        filepath=Path("dummy.md"),
        indexed_lines=[
            IndexedLine(line="Designing a Web Application", index=1),
        ],
    )
    assert len(checker.check(sec_courses)) == 0


def test_bracket_check():
    checker = BraketCheck()

    sec = Section(
        heading=Heading(text=SectionConstant.SUMMARY, heading_prefix="##"),
        filepath=Path("dummy.md"),
        indexed_lines=[
            IndexedLine(line="Title (detail)", index=1),
            IndexedLine(line="Title(detail)", index=2),
            IndexedLine(line="Title  (detail)", index=3),
            IndexedLine(line="Title ( detail)", index=4),
        ],
    )
    errors = checker.check(sec)
    assert len(errors) == 2
    assert errors[0].line_num == 3
    assert "Invalid spacing before open bracket" in errors[0].msg
    assert errors[1].line_num == 4
    assert "Space after open bracket" in errors[1].msg


def test_chronological_check():
    checker = ChronologicalCheck()

    # Work experience chron broken: older listed before newer
    sec_we = Section(
        heading=Heading(text=SectionConstant.WORK_EXPERIENCE, heading_prefix="##"),
        filepath=Path("dummy.md"),
        indexed_lines=[
            IndexedLine(line="**Tester** | _ASM_ | Jun 2007 - Aug 2007", index=1),
            IndexedLine(line="**Developer** | _AS Tall_ | Jan 2024 - Present", index=2),
        ],
    )
    errors = checker.check(sec_we)
    assert len(errors) == 1
    assert "Chronological order broken" in errors[0].msg


def test_format_check():
    checker = FormatCheck()

    # Work experience format mismatch (missing pipe separator)
    sec_we = Section(
        heading=Heading(text=SectionConstant.WORK_EXPERIENCE, heading_prefix="##"),
        filepath=Path("dummy.md"),
        indexed_lines=[IndexedLine(line="**Tester** _ASM_ | Jun 2007", index=1)],
    )
    errors = checker.check(sec_we)
    assert len(errors) == 1
    assert "format mismatch" in errors[0].msg

    # Courses format mismatch (2024 lacks short month name)
    sec_courses = Section(
        heading=Heading(text=SectionConstant.COURSES_AND_CERTIFICATES, heading_prefix="##"),
        filepath=Path("dummy.md"),
        indexed_lines=[IndexedLine(line="- Course | _Institution_ | 2024", index=1)],
    )
    errors = checker.check(sec_courses)
    assert len(errors) == 1
    assert "format mismatch" in errors[0].msg


def test_required_sections_check():
    checker = RequiredSectionsCheck()

    sections = [
        Section(heading=Heading(text=SectionConstant.WORK_EXPERIENCE, heading_prefix="##"), filepath=Path("dummy.md")),
        Section(heading=Heading(text="Projects", heading_prefix="##"), filepath=Path("dummy.md")),
    ]
    errors = checker.check_all(sections)
    assert len(errors) == 1
    assert "Missing 'courses and certificates' section" in errors[0].msg


def test_make_error():
    sec = Section(
        heading=Heading(text=SectionConstant.SUMMARY, heading_prefix="##"),
        filepath=Path("test_path.md"),
        indexed_lines=[],
    )
    line = IndexedLine(line="Sample line", index=42)
    err = make_error("An error occurred", sec, line)
    assert err.msg == "An error occurred"
    assert err.filepath == "test_path.md"
    assert err.line_num == 42
    assert err.line == "Sample line"


def test_duration_check():
    checker = DurationCheck()

    # Valid scenarios
    valid_sec = Section(
        heading=Heading(text=SectionConstant.SUMMARY, heading_prefix="##"),
        filepath=Path("dummy.md"),
        indexed_lines=[
            IndexedLine(line="Jan 2024", index=1),
            IndexedLine(line="Jan 2024 - Dec 2024", index=2),
            IndexedLine(line="Jan 2024 - Present", index=3),
            IndexedLine(line="No year mentioned here", index=4),
            IndexedLine(line="[Project 2024](https://github.com/user/project-2024) | Jan 2024", index=5),
            IndexedLine(line="[Project](https://github.com/user/project-2024)", index=6),
            # Testing that years in non-checked segments are ignored
            IndexedLine(line="**Project 2024** | Jun 2025", index=7),
        ],
    )
    assert len(checker.check(valid_sec)) == 0

    # Invalid scenarios
    invalid_sec = Section(
        heading=Heading(text=SectionConstant.SUMMARY, heading_prefix="##"),
        filepath=Path("dummy.md"),
        indexed_lines=[
            IndexedLine(line="2024", index=1),
            IndexedLine(line="2024 - Present", index=2),
            IndexedLine(line="Dec 2024 - 2025", index=3),
            IndexedLine(line="December 2024", index=4),
            IndexedLine(line="Jan 2024 - present", index=5),
        ],
    )
    errors = checker.check(invalid_sec)
    assert len(errors) == 5
    assert errors[0].line_num == 1
    assert errors[1].line_num == 2
    assert errors[2].line_num == 3
    assert errors[3].line_num == 4
    assert errors[4].line_num == 5


def test_check_cv_flag():
    # A list of sections missing required ones (e.g. 'work experience')
    sections = [
        Section(heading=Heading(text=SectionConstant.SUMMARY, heading_prefix="##"), filepath=Path("dummy.md")),
    ]

    # By default, is_cv is False, so RequiredSectionsCheck is not run
    errors_default = check(sections)
    assert len(errors_default) == 0

    # If is_cv is True, RequiredSectionsCheck runs and reports missing sections
    errors_cv = check(sections, is_cv=True)
    assert len(errors_cv) > 0
    assert any("Missing" in err.msg for err in errors_cv)

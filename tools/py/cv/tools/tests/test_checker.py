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
from md_tools.models import Line, Section, SectionConstant


def test_dot_check():
    sec1 = Section(
        name=SectionConstant.WORK_EXPERIENCE,
        md_prefix="##",
        filepath=Path("dummy.md"),
        raw_lines=[
            Line(raw_line="Senior developer.", number=1),
            Line(raw_line="Developing software", number=2),
        ],
    )
    checker = DotCheck()
    errors = checker.check(sec1)
    assert len(errors) == 1
    assert errors[0].line_num == 1
    assert "ends with a dot" in errors[0].msg

    sec2 = Section(
        name=SectionConstant.SUMMARY,
        md_prefix="##",
        filepath=Path("dummy.md"),
        raw_lines=[Line(raw_line="Experienced developer.", number=1)],
    )
    assert len(checker.check(sec2)) == 0


def test_two_space_check():
    checker = TwoSpaceCheck()

    sec_skills_err = Section(
        name=SectionConstant.SKILLS,
        md_prefix="##",
        filepath=Path("dummy.md"),
        raw_lines=[
            Line(raw_line="**Python**: advanced", number=1),
            Line(raw_line="**Go**: basic  ", number=2),
        ],
    )
    errors = checker.check(sec_skills_err)
    assert len(errors) == 1
    assert errors[0].line_num == 1
    assert "must end with exactly two spaces" in errors[0].msg

    sec_other_err = Section(
        name=SectionConstant.WORK_EXPERIENCE,
        md_prefix="##",
        filepath=Path("dummy.md"),
        raw_lines=[
            Line(raw_line="Senior Developer  ", number=1),
            Line(raw_line="Developing products", number=2),
        ],
    )
    errors = checker.check(sec_other_err)
    assert len(errors) == 1
    assert errors[0].line_num == 1
    assert "ends with two spaces" in errors[0].msg


def test_a_space_check():
    checker = ASpaceCheck()
    sec = Section(
        name=SectionConstant.SUMMARY,
        md_prefix="##",
        filepath=Path("dummy.md"),
        raw_lines=[
            Line(raw_line="This is a test.", number=1),
            Line(raw_line="This is another test.", number=2),
        ],
    )
    errors = checker.check(sec)
    assert len(errors) == 1
    assert "contains ' a '" in errors[0].msg

    sec_courses = Section(
        name=SectionConstant.COURSES_AND_CERTIFICATES,
        md_prefix="##",
        filepath=Path("dummy.md"),
        raw_lines=[
            Line(raw_line="Designing a Web Application", number=1),
        ],
    )
    assert len(checker.check(sec_courses)) == 0


def test_bracket_check():
    checker = BraketCheck()

    sec = Section(
        name=SectionConstant.SUMMARY,
        md_prefix="##",
        filepath=Path("dummy.md"),
        raw_lines=[
            Line(raw_line="Title (detail)", number=1),
            Line(raw_line="Title(detail)", number=2),
            Line(raw_line="Title  (detail)", number=3),
            Line(raw_line="Title ( detail)", number=4),
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
        name=SectionConstant.WORK_EXPERIENCE,
        md_prefix="##",
        filepath=Path("dummy.md"),
        raw_lines=[
            Line(raw_line="**Assembler** | _Fabek_ | Jun 2007 - Aug 2007", number=1),
            Line(raw_line="**Developer** | _AS Tallink_ | Jan 2024 - Present", number=2),
        ],
    )
    errors = checker.check(sec_we)
    assert len(errors) == 1
    assert "Chronological order broken" in errors[0].msg


def test_format_check():
    checker = FormatCheck()

    # Work experience format mismatch (missing pipe separator)
    sec_we = Section(
        name=SectionConstant.WORK_EXPERIENCE,
        md_prefix="##",
        filepath=Path("dummy.md"),
        raw_lines=[Line(raw_line="**Assembler** _Fabek_ | Jun 2007", number=1)],
    )
    errors = checker.check(sec_we)
    assert len(errors) == 1
    assert "format mismatch" in errors[0].msg

    # Courses format mismatch (2024 lacks short month name)
    sec_courses = Section(
        name=SectionConstant.COURSES_AND_CERTIFICATES,
        md_prefix="##",
        filepath=Path("dummy.md"),
        raw_lines=[Line(raw_line="- Course | _Institution_ | 2024", number=1)],
    )
    errors = checker.check(sec_courses)
    assert len(errors) == 1
    assert "format mismatch" in errors[0].msg


def test_required_sections_check():
    checker = RequiredSectionsCheck()

    sections = [
        Section(name=SectionConstant.WORK_EXPERIENCE, md_prefix="##", filepath=Path("dummy.md")),
        Section(name="Projects", md_prefix="##", filepath=Path("dummy.md")),
    ]
    errors = checker.check_all(sections)
    assert len(errors) == 1
    assert "Missing 'courses and certificates' section" in errors[0].msg


def test_make_error():
    sec = Section(
        name=SectionConstant.SUMMARY,
        md_prefix="##",
        filepath=Path("test_path.md"),
        raw_lines=[],
    )
    line = Line(raw_line="Sample line", number=42)
    err = make_error("An error occurred", sec, line)
    assert err.msg == "An error occurred"
    assert err.filepath == "test_path.md"
    assert err.line_num == 42
    assert err.line == "Sample line"


def test_duration_check():
    checker = DurationCheck()

    # Valid scenarios
    valid_sec = Section(
        name=SectionConstant.SUMMARY,
        md_prefix="##",
        filepath=Path("dummy.md"),
        raw_lines=[
            Line(raw_line="Jan 2024", number=1),
            Line(raw_line="Jan 2024 - Dec 2024", number=2),
            Line(raw_line="Jan 2024 - Present", number=3),
            Line(raw_line="No year mentioned here", number=4),
            Line(raw_line="[Project 2024](https://github.com/user/project-2024) | Jan 2024", number=5),
            Line(raw_line="[Project](https://github.com/user/project-2024)", number=6),
            # Testing that years in non-checked segments are ignored
            Line(raw_line="**Project 2024** | Jun 2025", number=7),
        ],
    )
    assert len(checker.check(valid_sec)) == 0

    # Invalid scenarios
    invalid_sec = Section(
        name=SectionConstant.SUMMARY,
        md_prefix="##",
        filepath=Path("dummy.md"),
        raw_lines=[
            Line(raw_line="2024", number=1),
            Line(raw_line="2024 - Present", number=2),
            Line(raw_line="Dec 2024 - 2025", number=3),
            Line(raw_line="December 2024", number=4),
            Line(raw_line="Jan 2024 - present", number=5),
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
        Section(name=SectionConstant.SUMMARY, md_prefix="##", filepath=Path("dummy.md")),
    ]

    # By default, is_cv is False, so RequiredSectionsCheck is not run
    errors_default = check(sections)
    assert len(errors_default) == 0

    # If is_cv is True, RequiredSectionsCheck runs and reports missing sections
    errors_cv = check(sections, is_cv=True)
    assert len(errors_cv) > 0
    assert any("Missing" in err.msg for err in errors_cv)

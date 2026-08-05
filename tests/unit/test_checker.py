from pathlib import Path

from job_hunt.resume.checker import (
    ASpaceCheck,
    BraketCheck,
    ChronologicalCheck,
    DotCheck,
    DuplicateEntryCheck,
    DuplicateLineCheck,
    DurationCheck,
    FormatCheck,
    ProjectFormatCheck,
    RequiredSectionsCheck,
    SectionNotEmptyCheck,
    TwoSpaceCheck,
    check,
    make_error,
)
from job_hunt.resume.models import SectionConstant
from job_hunt.resume.parse import Heading, IndexedLine, Section


def test_dot_check() -> None:
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


def test_two_space_check() -> None:
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
    assert TwoSpaceCheck._DEFAULT_ERROR_MSG in errors[0].msg

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
    assert TwoSpaceCheck._ERR_MSG_WRONG_ENDING in errors[0].msg


def test_a_space_check() -> None:
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


def test_bracket_check() -> None:
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


def test_chronological_check() -> None:
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


def test_format_check() -> None:
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


def test_required_sections_check() -> None:
    checker = RequiredSectionsCheck()

    sections = [
        Section(heading=Heading(text=SectionConstant.WORK_EXPERIENCE, heading_prefix="##"), filepath=Path("dummy.md")),
        Section(heading=Heading(text="Projects", heading_prefix="##"), filepath=Path("dummy.md")),
    ]
    errors = checker.check_all(sections)
    assert len(errors) == 1
    assert "Missing 'courses and certificates' section" in errors[0].msg


def test_make_error() -> None:
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


def test_duration_check() -> None:
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


def test_check_resume_flag() -> None:
    # A list of sections missing required ones (e.g. 'work experience')
    sections = [
        Section(heading=Heading(text=SectionConstant.SUMMARY, heading_prefix="##"), filepath=Path("dummy.md")),
    ]

    # By default, is_resume is False, so RequiredSectionsCheck is not run
    errors_default = check(sections)
    assert len(errors_default) == 0

    # If is_resume is True, RequiredSectionsCheck runs and reports missing sections
    errors_resume = check(sections, is_resume=True)
    assert len(errors_resume) > 0
    assert any("Missing" in err.msg for err in errors_resume)


def test_duplicate_entry_check_work_experience() -> None:
    checker = DuplicateEntryCheck()
    sec = Section(
        heading=Heading(text=SectionConstant.WORK_EXPERIENCE, heading_prefix="##"),
        filepath=Path("dummy.md"),
        indexed_lines=[
            IndexedLine(line="**Tester** | _ASM_ | Jun 2007 - Aug 2007", index=1),
            IndexedLine(line="- Did testing", index=2),
            IndexedLine(line="**Tester** | _ASM_ | Jun 2007 - Aug 2007", index=3),
            IndexedLine(line="- Did testing again", index=4),
        ],
    )
    errors = checker.check(sec)
    assert len(errors) == 1
    assert "Duplicate entry" in errors[0].msg


def test_duplicate_entry_check_projects() -> None:
    checker = DuplicateEntryCheck()
    sec = Section(
        heading=Heading(text=SectionConstant.PERSONAL_PROJECTS, heading_prefix="##"),
        filepath=Path("dummy.md"),
        indexed_lines=[
            IndexedLine(line="**[Cool App](https://github.com/x/cool)** | Jun 2025", index=1),
            IndexedLine(line="- Built the thing", index=2),
            IndexedLine(line="- Skills: Python", index=3),
            IndexedLine(line="**[Cool App](https://github.com/x/cool)** | Jun 2025", index=4),
            IndexedLine(line="- Built it again", index=5),
            IndexedLine(line="- Skills: Python", index=6),
        ],
    )
    errors = checker.check(sec)
    assert len(errors) == 1
    assert "Duplicate entry" in errors[0].msg


def test_duplicate_entry_check_courses() -> None:
    checker = DuplicateEntryCheck()
    sec = Section(
        heading=Heading(text=SectionConstant.COURSES_AND_CERTIFICATES, heading_prefix="##"),
        filepath=Path("dummy.md"),
        indexed_lines=[
            IndexedLine(line="- AWS Certified | _AWS_ | Jan 2024", index=1),
            IndexedLine(line="- AWS Certified | _AWS_ | Jan 2024", index=2),
        ],
    )
    errors = checker.check(sec)
    assert len(errors) == 1
    assert "Duplicate entry" in errors[0].msg


def test_duplicate_line_check() -> None:
    checker = DuplicateLineCheck()
    sec = Section(
        heading=Heading(text=SectionConstant.WORK_EXPERIENCE, heading_prefix="##"),
        filepath=Path("dummy.md"),
        indexed_lines=[
            IndexedLine(line="- Built pipelines", index=1),
            IndexedLine(line="- Built pipelines", index=2),
            IndexedLine(line="\\hfill", index=3),
            IndexedLine(line="", index=4),
        ],
    )
    errors = checker.check(sec)
    assert len(errors) == 1
    assert errors[0].line_num == 2
    assert "Duplicate line" in errors[0].msg


def test_project_format_check_handles_hfill() -> None:
    # \hfill is the date separator persisted by fix_markdown - entries using it must still parse.
    checker = ProjectFormatCheck()
    sec = Section(
        heading=Heading(text=SectionConstant.PERSONAL_PROJECTS, heading_prefix="##"),
        filepath=Path("dummy.md"),
        indexed_lines=[
            IndexedLine(line="**[Cool App](https://github.com/x/cool)** \\hfill Jun 2025", index=1),
            IndexedLine(line="- Built the thing", index=2),
            IndexedLine(line="- Skills: Python", index=3),
        ],
    )
    assert len(checker.check(sec)) == 0


def test_project_format_check() -> None:
    checker = ProjectFormatCheck()

    incomplete_sec = Section(
        heading=Heading(text=SectionConstant.PERSONAL_PROJECTS, heading_prefix="##"),
        filepath=Path("dummy.md"),
        indexed_lines=[
            IndexedLine(line="**[Cool App](https://github.com/x/cool)** | Jun 2025", index=1),
        ],
    )
    errors = checker.check(incomplete_sec)
    assert len(errors) == 2
    assert any("no bullet points" in e.msg for e in errors)
    assert any("no Skills line" in e.msg for e in errors)

    complete_sec = Section(
        heading=Heading(text=SectionConstant.PERSONAL_PROJECTS, heading_prefix="##"),
        filepath=Path("dummy.md"),
        indexed_lines=[
            IndexedLine(line="**[Cool App](https://github.com/x/cool)** | Jun 2025", index=1),
            IndexedLine(line="- Built the thing", index=2),
            IndexedLine(line="- Skills: Python", index=3),
        ],
    )
    assert len(checker.check(complete_sec)) == 0


def test_section_not_empty_check() -> None:
    checker = SectionNotEmptyCheck()

    empty_sections = [
        Section(
            heading=Heading(text=SectionConstant.COURSES_AND_CERTIFICATES, heading_prefix="##"),
            filepath=Path("dummy.md"),
        ),
        Section(heading=Heading(text="Personal projects", heading_prefix="##"), filepath=Path("dummy.md")),
    ]
    errors = checker.check_all(empty_sections)
    assert len(errors) == 2
    assert all("no entries" in e.msg for e in errors)

    filled_sections = [
        Section(
            heading=Heading(text=SectionConstant.COURSES_AND_CERTIFICATES, heading_prefix="##"),
            filepath=Path("dummy.md"),
            indexed_lines=[IndexedLine(line="- AWS Certified | _AWS_ | Jan 2024", index=1)],
        ),
        Section(
            heading=Heading(text=SectionConstant.PERSONAL_PROJECTS, heading_prefix="##"),
            filepath=Path("dummy.md"),
            indexed_lines=[IndexedLine(line="**[Cool App](https://github.com/x/cool)** | Jun 2025", index=1)],
        ),
    ]
    assert len(checker.check_all(filled_sections)) == 0

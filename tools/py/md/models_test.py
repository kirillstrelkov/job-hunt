from pathlib import Path

import pytest

from md.models import (
    Body,
    BulletPoint,
    CourseOrCertificateEntry,
    Degree,
    Duration,
    Footer,
    LanguageEntry,
    PersonalProjectsEntry,
    Skill,
    SkillGroup,
    Summary,
    Thesis,
    Title,
    WorkExperienceEntry,
    get_md_title,
)


def test_get_md_title() -> None:
    assert get_md_title("# Title 2\nContent") == Title(prefix="#", text="Title 2")
    assert get_md_title("## Title 2\nContent") == Title(prefix="##", text="Title 2")
    assert get_md_title("### Title 2\nContent") == Title(prefix="###", text="Title 2")
    assert get_md_title("previous lines\n# Title 2\nContent") == Title(prefix="#", text="Title 2")


def test_duration_roundtrip() -> None:
    # Test single date
    d1 = Duration.from_string("Sep 2022")
    assert d1.start_date is None
    assert d1.end_date == "Sep 2022"
    assert d1.to_string() == "Sep 2022"

    # Test range with backslash-escaped hyphen
    d2 = Duration.from_string("Jun 2007 \\- Aug 2007")
    assert d2.start_date == "Jun 2007"
    assert d2.end_date == "Aug 2007"
    assert d2.to_string() == "Jun 2007 \\- Aug 2007"

    # Test range with standard hyphen
    d3 = Duration.from_string("Jan 2024 - Present")
    assert d3.start_date == "Jan 2024"
    assert d3.end_date == "Present"
    assert d3.to_string() == "Jan 2024 \\- Present"


def test_bullet_point_roundtrip() -> None:
    bp = BulletPoint.from_string("- Developed an interactive dashboard application")
    assert bp.text == "Developed an interactive dashboard application"
    assert bp.to_string() == "- Developed an interactive dashboard application"

    bp2 = BulletPoint.from_string("No prefix text")
    assert bp2.text == "No prefix text"
    assert bp2.to_string() == "- No prefix text"


def test_skill_roundtrip() -> None:
    s = Skill.from_string("Python")
    assert s.text == "Python"
    assert s.to_string() == "Python"


def test_thesis_roundtrip() -> None:
    t = Thesis.from_string("- Thesis: [Automated web test framework development](https://example.com/thesis.pdf)")
    assert t.name == "Automated web test framework development"
    assert t.url == "https://example.com/thesis.pdf"
    assert t.to_string() == "- Thesis: [Automated web test framework development](https://example.com/thesis.pdf)"


def test_language_roundtrip() -> None:
    lang = LanguageEntry.from_string("**German**: B2 (Upper Intermediate)")
    assert lang.name == "German"
    assert lang.level == "B2 (Upper Intermediate)"
    assert lang.to_string() == "**German**: B2 (Upper Intermediate)"


def test_degree_roundtrip() -> None:
    s = (
        "**Bachelor of Science in Computer Science** | _Technical University of Munich, Germany_ \\hfill 2010 \\- 2014"
        "\n\n- Thesis: [Automated web test framework development](https://example.com/thesis.pdf)"
    )
    deg = Degree.from_string(s)
    assert deg.degree == "Bachelor of Science in Computer Science"
    assert deg.institution == "Technical University of Munich, Germany"
    assert deg.duration.start_date == "2010"
    assert deg.duration.end_date == "2014"
    assert deg.thesis is not None
    assert deg.thesis.name == "Automated web test framework development"
    assert deg.to_string().strip() == s.strip()


def test_degree_from_string_variants() -> None:
    # Test degree without thesis
    s1 = "**Master of Science** | _Stanford University_ \\hfill 2015 \\- 2017"
    deg1 = Degree.from_string(s1)
    assert deg1.degree == "Master of Science"
    assert deg1.institution == "Stanford University"
    assert deg1.duration.start_date == "2015"
    assert deg1.duration.end_date == "2017"
    assert deg1.thesis is None

    # Test spacing and hfill variants
    s2 = "**Ph.D. in Physics**| _MIT_\\hfill2018\\-2022"
    deg2 = Degree.from_string(s2)
    assert deg2.degree == "Ph.D. in Physics"
    assert deg2.institution == "MIT"
    assert deg2.duration.start_date == "2018"
    assert deg2.duration.end_date == "2022"

    # Test empty string raises ValueError
    with pytest.raises(ValueError, match="Empty string for Degree"):
        Degree.from_string("   \n   ")


def test_work_experience_roundtrip() -> None:
    s1 = (
        "**Tester** | _Fabek Elektroonika OÜ, Tallinn, Estonia_ | Jun 2007 \\- Aug 2007\n\n"
        "- Assembled and packaged electronic devices\n"
        "- Performed wire soldering for hardware devices\n\n"
        "> _Reason for resignation: studies_"
    )
    we1 = WorkExperienceEntry.from_string(s1)
    assert we1.title == "Tester"
    assert we1.company == "Fabek Elektroonika OÜ"
    assert we1.location == "Tallinn, Estonia"
    assert we1.duration.start_date == "Jun 2007"
    assert we1.duration.end_date == "Aug 2007"
    assert len(we1.bullet_points) == 2
    assert we1.reason_for_resignation == "studies"
    assert we1.skills is None
    assert we1.to_string().strip() == s1.strip()

    s2 = (
        "**Junior Developer** | _AS Tallink Group, Tallinn, Estonia_ | Jun 2013 \\- Jun 2013\n\n"
        "- 12-days practical work to finalize Java course\n"
        "- Investigated and fixed bugs for Java XML/XSLT conversion engine and implemented additional unit tests\n"
        "- Skills: XML, XSLT, TDD, Java, JUnit, Mockito, oXygen XML Editor"
    )
    we2 = WorkExperienceEntry.from_string(s2)
    assert we2.title == "Junior Developer"
    assert we2.company == "AS Tallink Group"
    assert we2.location == "Tallinn, Estonia"
    assert we2.duration.start_date == "Jun 2013"
    assert we2.duration.end_date == "Jun 2013"
    assert len(we2.bullet_points) == 2
    assert we2.reason_for_resignation is None
    assert we2.skills is not None
    assert len(we2.skills) == 7
    assert we2.skills[0].text == "XML"
    assert we2.skills[6].text == "oXygen XML Editor"
    assert we2.to_string().strip() == s2.strip()


def test_personal_projects_roundtrip() -> None:
    s = (
        "**[Employee Polls Web App](https://github.com/kirillstrelkov/employee-pools)** | Sep 2022\n\n"
        "- Developed an interactive dashboard application allowing users to create, answer and visualize results "
        "for internal polls\n"
        "- Implemented a responsive UI with Material-UI (MUI) and managed complex application state using Redux "
        "and React Redux\n"
        "- Configured client-side routing and ensured application reliability through comprehensive unit testing\n"
        "- Skills: JavaScript (ES6+), React, React Redux, Redux Middleware/Thunk, React Router, Material-UI (MUI), "
        "Jest, HTML5/CSS3, Git"
    )
    pp = PersonalProjectsEntry.from_string(s)
    assert pp.name == "Employee Polls Web App"
    assert pp.url == "https://github.com/kirillstrelkov/employee-pools"
    assert pp.duration.start_date is None
    assert pp.duration.end_date == "Sep 2022"
    assert len(pp.bullet_points) == 3
    assert len(pp.skills) == 9
    assert pp.skills[0].text == "JavaScript (ES6+)"
    assert pp.skills[8].text == "Git"
    assert pp.to_string().strip() == s.strip()


def test_courses_and_certificates_roundtrip() -> None:
    s = "- Agentic AI Nanodegree | _Udacity_ | Jul 2026"
    cc = CourseOrCertificateEntry.from_string(s)
    assert cc.name == "Agentic AI Nanodegree"
    assert cc.institution == "Udacity"
    assert cc.duration.start_date is None
    assert cc.duration.end_date == "Jul 2026"
    assert cc.to_string() == s


def test_summary_roundtrip() -> None:
    s = "## Summary\n\nExperienced software engineer with a track record of developing scalable applications."
    sum_obj = Summary.from_string(s, Path("fake"), [])
    assert sum_obj.text == "Experienced software engineer with a track record of developing scalable applications."
    assert sum_obj.to_string() == s


def test_skills_roundtrip() -> None:
    s = "## Skills\n\n**Languages**: Python, Go | **Cloud & DevOps**: AWS, Docker"
    skills_obj = SkillGroup.from_string(s)
    assert len(skills_obj.groups) == 2
    assert skills_obj.groups[0].name == "Languages"
    assert len(skills_obj.groups[0].skills) == 2
    assert skills_obj.groups[0].skills[0].text == "Python"
    assert skills_obj.groups[1].name == "Cloud & DevOps"
    assert len(skills_obj.groups[1].skills) == 2
    assert skills_obj.groups[1].skills[1].text == "Docker"
    assert skills_obj.to_string() == s


def test_footer_multiple_degrees() -> None:
    s = """
## Education

**Master of Science in Computer Science** | _Stanford University_ \\hfill 2015 \\- 2017
- Thesis: [Deep Learning](https://example.com/thesis1.pdf)

**Bachelor of Science** | _MIT_ \\hfill 2011 \\- 2015
- Thesis: [Robotics](https://example.com/thesis2.pdf)

## Languages
**English**: Native, **Spanish**: A2
"""
    footer = Footer.from_string(s, Path("fake"), [])
    assert len(footer.educations) == 2
    assert footer.educations[0].degree == "Master of Science in Computer Science"
    assert footer.educations[0].institution == "Stanford University"
    assert footer.educations[0].thesis is not None
    assert footer.educations[0].thesis.name == "Deep Learning"

    assert footer.educations[1].degree == "Bachelor of Science"
    assert footer.educations[1].institution == "MIT"
    assert footer.educations[1].thesis is not None
    assert footer.educations[1].thesis.name == "Robotics"

    assert len(footer.languages) == 2
    assert footer.languages[0].name == "English"
    assert footer.languages[0].level == "Native"
    assert footer.languages[1].name == "Spanish"
    assert footer.languages[1].level == "A2"


def test_body_multiple_certificates() -> None:
    s = """
## Courses and certificates

- Certified Kubernetes Application Developer | _Cloud Native Computing Foundation_ | Feb 2026
- AWS Certified Solutions Architect | _Amazon Web Services_ | Jan 2025

""".strip()
    body = Body.from_string(s, Path("fake"), [])
    assert len(body.courses_and_certificates) == 2

    c1 = body.courses_and_certificates[0]
    assert c1.name == "Certified Kubernetes Application Developer"
    assert c1.institution == "Cloud Native Computing Foundation"
    assert c1.duration.start_date is None
    assert c1.duration.end_date == "Feb 2026"

    c2 = body.courses_and_certificates[1]
    assert c2.name == "AWS Certified Solutions Architect"
    assert c2.institution == "Amazon Web Services"
    assert c2.duration.start_date is None
    assert c2.duration.end_date == "Jan 2025"

    assert s == body.to_string().strip()

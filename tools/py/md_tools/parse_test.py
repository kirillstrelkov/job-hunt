from pathlib import Path

from md_tools.models import Body, Footer, Header, parse


def test_parse_header_example() -> None:
    filepath = Path("cv/example/header.md")
    content = filepath.read_text(encoding="utf-8")

    header = Header.from_string(content)
    assert header.name == "John Doe"
    assert header.address == "Berlin, Germany"
    assert header.email == "john.doe@example.com"
    assert header.telephone == "+49 123 4567890"
    assert header.linkedin == "https://www.linkedin.com/in/johndoe/"
    assert header.github == "https://github.com/johndoe"

    # Check roundtrip
    assert header.to_string().strip() == content.strip()


def test_parse_body_example() -> None:
    filepath = Path("cv/example/body.md")
    content = filepath.read_text(encoding="utf-8")

    body = Body.from_string(content)
    assert len(body.work_experience) == 7
    assert len(body.personal_projects) == 5
    assert len(body.courses_and_certificates) == 23

    # Check some details of the first work experience
    we = body.work_experience[0]
    assert we.title == "Senior Software Engineer"
    assert we.company == "Global Tech Solutions Inc."
    assert we.location == "Berlin, Germany"
    assert we.duration.start_date == "Jan 2024"
    assert we.duration.end_date == "Present"

    # Check some details of the first personal project
    pp = body.personal_projects[0]
    assert pp.name == "Cloud-Native API Gateway"
    assert pp.url == "https://github.com/johndoe/cloud-gateway"
    assert pp.duration.start_date is None
    assert pp.duration.end_date == "Jun 2025"

    # Check some details of the first course
    cc = body.courses_and_certificates[0]
    assert cc.name == "Certified Kubernetes Application Developer"
    assert cc.institution == "Cloud Native Computing Foundation"
    assert cc.duration.start_date is None
    assert cc.duration.end_date == "Feb 2026"

    # Let's compare normalized roundtrip
    normalized_content = content.replace(" \\- ", " - ").strip()
    normalized_output = body.to_string().replace(" \\- ", " - ").strip()
    assert normalized_output == normalized_content


def test_parse_footer_example() -> None:
    filepath = Path("cv/example/footer.md")
    content = filepath.read_text(encoding="utf-8")

    footer = Footer.from_string(content)
    assert len(footer.educations) == 1
    assert len(footer.languages) == 3

    deg = footer.educations[0]
    assert deg.degree == "Bachelor of Science in Computer Science"
    assert deg.institution == "Technical University of Munich, Germany"
    assert deg.duration.start_date == "2010"
    assert deg.duration.end_date == "2014"
    assert deg.thesis is not None
    assert deg.thesis.name == "Automated web test framework development"
    assert deg.thesis.url == "https://example.com/thesis.pdf"

    l1, l2, l3 = footer.languages
    assert l1.name == "English"
    assert l1.level == "Native"
    assert l2.name == "German"
    assert l2.level == "B2 (Upper Intermediate)"
    assert l3.name == "Spanish"
    assert l3.level == "A2 (Elementary)"

    # Normalize for comparison
    normalized_content = content.replace(" \\- ", " - ").strip()
    normalized_output = footer.to_string().replace(" \\- ", " - ").strip()
    assert normalized_output == normalized_content


def test_parse_full_cv() -> None:
    header_text = Path("cv/example/header.md").read_text(encoding="utf-8")
    body_text = Path("cv/example/body.md").read_text(encoding="utf-8")
    footer_text = Path("cv/example/footer.md").read_text(encoding="utf-8")

    full_cv_text = f"{header_text}\n\n{body_text}\n\n{footer_text}"
    cv_obj = parse(full_cv_text)

    assert cv_obj.header is not None
    assert cv_obj.header.name == "John Doe"
    assert len(cv_obj.body.work_experience) == 7
    assert len(cv_obj.footer.languages) == 3

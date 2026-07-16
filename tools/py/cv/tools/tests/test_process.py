from cv.tools.process_cv import fix_markdown


def test_do_fix() -> None:
    cv_md = """
# John Doe

Berlin, Germany | <john.doe@example.com> | +49 123 4567890\\
[linkedin.com/in/johndoe](https://www.linkedin.com/in/johndoe/) | [github.com/johndoe](https://github.com/johndoe)

---

## Summary

Software Engineer with extensive experience in designing and implementing automated test frameworks.
Proficient in Java, Go, TypeScript, and Python.

## Skills

**Languages**: Java, Go, TypeScript, Python, C++, Ruby
**Databases**: PostgreSQL, MongoDB

## Work experience

**Senior Software Engineer** | _Global Tech Solutions Inc., Berlin, Germany_ | Jan 2024 - Present

- Lead the development of distributed backend services using Python, Go, and PostgreSQL.
- Architect and maintain robust CI/CD pipelines utilizing GitHub Actions, Docker, and Kubernetes
- Optimize application performance, reducing API response times by 35% through query optimization and caching
- Mentor junior and mid-level engineers, establishing coding standards and conducting regular code reviews
- Skills: Python, Go, Docker, Kubernetes, PostgreSQL, Git, CI/CD, AWS

## Personal projects

**[Cloud-Native API Gateway](https://github.com/johndoe/cloud-gateway)** | Jun 2025

- Built a high-performance API gateway in Go supporting rate limiting, request forwarding, and JWT authentication
- Configured automated deployment manifests for Kubernetes clusters using Helm
- Skills: Go, Kubernetes, Helm, Docker, JWT

## Courses and certificates

- Certified Kubernetes Application Developer | _Cloud Native Computing Foundation_ | Feb 2026
- Advanced System Design & Architecture | _Coursera_ | 2024
- Go Developer Bootcamp | _Udemy_ | 2023
- Generative AI Nanodegree | _Udacity_ | 2026
- Apache Flink Fundamentals | _Confluent_ | 2026

---

## Education

**Bachelor of Science in Computer Science** | _Technical University of Munich, Germany_ | Sep 2010 - Sep 2014

## Languages

**English**: Native, **German**: B2 (Upper Intermediate), **Spanish**: A2 (Elementary)

    """
    fixed_md = fix_markdown(cv_md)
    assert cv_md != fixed_md
    assert r"+49 123 4567890\\" in fixed_md, "Phone should end with \\"
    for hfill in [
        r"Germany_ \hfill Jan",
        r"cloud-gateway)** \hfill Jun 2025",
        r"Foundation_ \hfill Feb 2026",
        r"Munich, Germany_ \hfill Sep 2010",
    ]:
        assert hfill in fixed_md, r"| should be replaced \hfill"

    assert ", Ruby\\" in fixed_md, "Skills should end with \\"
    assert ", MongoDB\\" in fixed_md, "Skills should end with \\"

    assert "automated test frameworks." in fixed_md, "Dot should be in Summary"

    assert "Python, Go, and PostgreSQL." not in fixed_md, "Should not end with dot"

    # TODO run do check over fixed cv

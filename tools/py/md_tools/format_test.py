from md_tools.format import format


def test_format_courses_equivalence() -> None:
    md = r"""## Courses and certificates

- Agentic AI Nanodegree | _Udacity_ \hfill Jul 2026

---

"""
    res = format(md)
    assert res == md

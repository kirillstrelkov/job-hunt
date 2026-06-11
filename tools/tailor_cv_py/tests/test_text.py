from tailor_cv.text import to_plain_text


def test_strips_headers():
    assert to_plain_text("## Senior Engineer\nsome text") == "Senior Engineer\nsome text"


def test_strips_bold_and_italic():
    assert to_plain_text("**required** and _preferred_") == "required and preferred"


def test_strips_markdown_links():
    assert to_plain_text("[Apply here](https://example.com)") == "Apply here"


def test_strips_html_tags():
    assert to_plain_text("<p>Job description</p>") == "Job description"


def test_strips_inline_code():
    assert to_plain_text("Use `Python` or `Go`") == "Use Python or Go"


def test_plain_text_unchanged():
    text = "We are looking for a senior engineer.\n\nRequirements:\n- 5 years experience"
    assert to_plain_text(text) == text


def test_collapses_excess_blank_lines():
    assert to_plain_text("line1\n\n\n\nline2") == "line1\n\nline2"

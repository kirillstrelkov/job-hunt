from tailor_cv.prompt import (
    COVER_LETTER_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    build_cover_letter_message,
    build_user_message,
)


def test_user_message_contains_cv_and_jd():
    msg = build_user_message(master_cv="My CV content", job_description="Senior Dev role")
    assert "My CV content" in msg
    assert "Senior Dev role" in msg


def test_system_prompt_contains_instructions():
    assert "Markdown" in SYSTEM_PROMPT
    assert "NO HALLUCINATIONS" in SYSTEM_PROMPT


def test_system_prompt_has_no_placeholder():
    assert "{cv}" not in SYSTEM_PROMPT
    assert "{job_description}" not in SYSTEM_PROMPT


def test_cover_letter_message_contains_cv_and_jd():
    msg = build_cover_letter_message(master_cv="My CV", job_description="Dev role")
    assert "My CV" in msg
    assert "Dev role" in msg


def test_cover_letter_system_prompt_has_no_placeholder():
    assert "{cv}" not in COVER_LETTER_SYSTEM_PROMPT
    assert "{job_description}" not in COVER_LETTER_SYSTEM_PROMPT

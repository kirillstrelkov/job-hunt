from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load(filename: str) -> str:
    return (_PROMPTS_DIR / filename).read_text(encoding="utf-8")


SYSTEM_PROMPT = _load("cv_system.txt")
USER_TEMPLATE = _load("cv_user.txt")

COVER_LETTER_SYSTEM_PROMPT = _load("cover_letter_system.txt")
COVER_LETTER_USER_TEMPLATE = _load("cover_letter_user.txt")


DEFAULT_HEADER = _PROMPTS_DIR / "default_header.md"
DEFAULT_FOOTER = _PROMPTS_DIR / "default_footer.md"


def build_user_message(master_cv: str, job_description: str) -> str:
    return USER_TEMPLATE.format(cv=master_cv, job_description=job_description)


def build_cover_letter_message(master_cv: str, job_description: str) -> str:
    return COVER_LETTER_USER_TEMPLATE.format(cv=master_cv, job_description=job_description)

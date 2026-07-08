from md_parser.models import CV


def parse(text: str) -> CV:
    """Parse CV markdown text into a CV Pydantic model.

    Args:
        text: The raw markdown content of the CV.

    Returns:
        CV: The parsed CV Pydantic model.

    """
    return CV.from_string(text)

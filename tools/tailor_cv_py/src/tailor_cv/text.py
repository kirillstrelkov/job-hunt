import re


def to_plain_text(text: str) -> str:
    """Strip common markdown and HTML formatting, leaving clean plain text."""
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Remove markdown links: [label](url) -> label
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Remove inline code and code fences
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    # Remove ATX headers (# ## ###)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Remove bold/italic markers (**, __, *, _)
    text = re.sub(r"(\*{1,3}|_{1,3})(.+?)\1", r"\2", text)
    # Remove horizontal rules
    text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)
    # Normalize whitespace: collapse 3+ blank lines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

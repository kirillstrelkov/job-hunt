"""Markdown formatting module using mdformat."""

import mdformat


def format(md: str) -> str:
    """Format markdown text as a string using mdformat.

    Args:
        md: The raw markdown content.

    Returns:
        str: The formatted markdown text.

    """
    return mdformat.text(md)

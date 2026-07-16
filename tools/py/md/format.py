"""Markdown formatting module using mdformat."""

import mdformat


def format(md: str, *, fix_latex_commands: bool = True) -> str:
    """Format markdown text as a string using mdformat.

    Args:
        md: The raw markdown content.
        fix_latex_commands: Whether to fix latex commands.

    Returns:
        str: The formatted markdown text.

    """
    fmt_text = mdformat.text(md)
    if fix_latex_commands:
        fmt_text = fmt_text.replace(r"\\hfill", r"\hfill")
    return fmt_text

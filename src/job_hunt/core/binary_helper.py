"""Centralized binary discovery and resolution helper for system executables."""

import os
import shutil
from enum import StrEnum
from pathlib import Path

DEFAULT_BINARY_HINTS: dict[str, str] = {
    "pandoc": "Please install Pandoc (e.g. 'brew install pandoc' or 'sudo apt-get install pandoc').",
    "pdfinfo": "Please install poppler-utils (e.g. 'brew install poppler' or 'sudo apt-get install poppler-utils').",
    "pdftotext": "Please install poppler-utils (e.g. 'brew install poppler' or 'sudo apt-get install poppler-utils').",
    "npx": "Please install Node.js and npm (e.g. 'brew install node' or https://nodejs.org/).",
    "streamlit": "Please install streamlit in your python environment (e.g. 'uv pip install streamlit').",
    "codesign": "codesign is a macOS system utility.",
}


class BinaryNotFoundError(FileNotFoundError):
    """Raised when a required system binary executable is not found on system PATH."""

    def __init__(self, binary_name: str, hint: str | None = None) -> None:
        msg = f"Required binary '{binary_name}' was not found in system PATH."
        if hint:
            msg += f" {hint}"
        super().__init__(msg)
        self.binary_name = binary_name


class BinaryName(StrEnum):
    """Enumeration of external system binaries used by the project."""

    PANDOC = "pandoc"
    PDFINFO = "pdfinfo"
    PDFTOTEXT = "pdftotext"
    NPX = "npx"
    STREAMLIT = "streamlit"
    CODESIGN = "codesign"


def _resolve_npx() -> str | None:
    """Attempt to resolve npx from system PATH or NVM directories."""
    resolved = shutil.which("npx")
    if resolved:
        return resolved

    home = Path.home()
    nvm_dir = home / ".nvm" / "versions" / "node"
    if nvm_dir.exists():
        node_versions = sorted(nvm_dir.glob("v*"), reverse=True)
        for version in node_versions:
            npx_bin = version / "bin" / "npx"
            if npx_bin.exists():
                os.environ["PATH"] = str(version / "bin") + os.pathsep + os.environ.get("PATH", "")
                return str(npx_bin)
    return None


def get_binary(
    name: str | BinaryName,
    *,
    hint: str | None = None,
    required: bool = True,
) -> str:
    """Resolve the path to a system binary executable.

    Args:
        name: Name or enum of the binary executable.
        hint: Optional custom guidance for installing or resolving the binary.
        required: Whether to raise BinaryNotFoundError when the binary is not found.

    Returns:
        The resolved absolute path string to the executable.

    Raises:
        BinaryNotFoundError: If required is True and the binary is not found.

    """
    bin_name = name.value if isinstance(name, BinaryName) else str(name)
    resolved = _resolve_npx() if bin_name == BinaryName.NPX else shutil.which(bin_name)

    if not resolved:
        if not required:
            return ""
        error_hint = hint or DEFAULT_BINARY_HINTS.get(bin_name)
        raise BinaryNotFoundError(bin_name, hint=error_hint)

    return resolved


def get_pandoc(hint: str | None = None) -> str:
    """Resolve pandoc binary."""
    return get_binary(BinaryName.PANDOC, hint=hint)


def get_pdfinfo(hint: str | None = None) -> str:
    """Resolve pdfinfo binary."""
    return get_binary(BinaryName.PDFINFO, hint=hint)


def get_pdftotext(hint: str | None = None) -> str:
    """Resolve pdftotext binary."""
    return get_binary(BinaryName.PDFTOTEXT, hint=hint)


def get_npx(hint: str | None = None) -> str:
    """Resolve npx binary."""
    return get_binary(BinaryName.NPX, hint=hint)


def get_streamlit(hint: str | None = None) -> str:
    """Resolve streamlit binary."""
    return get_binary(BinaryName.STREAMLIT, hint=hint)


def get_codesign(hint: str | None = None, *, required: bool = True) -> str:
    """Resolve codesign binary."""
    return get_binary(BinaryName.CODESIGN, hint=hint, required=required)

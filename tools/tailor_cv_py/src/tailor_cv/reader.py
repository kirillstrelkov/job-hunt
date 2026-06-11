from pathlib import Path


def read_file(path: str) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")
    content = p.read_text(encoding="utf-8").strip()
    if not content:
        raise ValueError(f"File is empty: {path}")
    return content

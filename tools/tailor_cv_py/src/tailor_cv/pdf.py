import subprocess

from loguru import logger


def convert_to_pdf(md_path: str, pdf_path: str) -> None:
    logger.info(f"Converting {md_path} → {pdf_path} via pandoc")
    result = subprocess.run(
        [
            "pandoc",
            "-f",
            "markdown",
            "-t",
            "pdf",
            "-V",
            "geometry:margin=1.5cm",
            md_path,
            "-o",
            pdf_path,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"pandoc failed:\n{result.stderr}")

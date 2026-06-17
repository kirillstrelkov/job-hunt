#!/usr/bin/env python3
import argparse
from pathlib import Path

from loguru import logger

from cfg import DEFAULT_CONFIG


def prepare_cv(folder: str, tailored_cv_body: str | None, llm_prompt: bool = False) -> None:
    folder_path = Path(folder)
    if not folder_path.exists():
        raise FileNotFoundError(f"{folder_path} not found")

    # inputs
    body = folder_path / "body.md"

    header = DEFAULT_CONFIG.header
    footer = DEFAULT_CONFIG.footer
    mastercv = DEFAULT_CONFIG.body
    tailor_for_desc = DEFAULT_CONFIG.prompt
    jd = folder_path / "jd.txt"

    paths_to_check = [
        header,
        footer,
        tailor_for_desc,
        mastercv,
    ]

    if tailored_cv_body:
        paths_to_check.append(body)

    if llm_prompt:
        paths_to_check.append(jd)

    for p in paths_to_check:
        if not p.exists():
            raise FileNotFoundError(f"{p} not found")

    # outputs
    out_folder = folder_path / "gen"
    if not out_folder.exists():
        out_folder.mkdir(exist_ok=False)

    tailored_llm_text = out_folder / "llm_prompt.txt"
    cv_out = out_folder / "cv.md"

    # generate
    if llm_prompt:
        logger.info(f"Generating : {tailored_llm_text}")

        content = tailor_for_desc.read_text().format(
            master_cv=(mastercv).read_text(),
            job_description=(jd).read_text(),
        )
        tailored_llm_text.write_text(content)

        logger.info(f"Written: {tailored_llm_text}")

    if tailored_cv_body:
        logger.info(f"Generating : {cv_out}")

        tailored_cv_body_path = Path(tailored_cv_body)
        assert tailored_cv_body_path.exists()

        with cv_out.open("w") as out:
            out.write((header).read_text())
            out.write("\n")

            out.write((body).read_text())
            out.write("\n")

            out.write((footer).read_text())
        logger.info(f"Written: {tailored_cv_body_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Assemble CV from header, body and footer.")
    parser.add_argument("folder", help="Path to the CV folder containing body.md")
    parser.add_argument(
        "--tailored-cv-body",
        required=False,
        default=None,
        help="Path to tailored CV body - body.md",
    )
    parser.add_argument(
        "--llm-prompt",
        action="store_true",
        default=False,
        help="Create llm_prompt.txt",
    )

    args = parser.parse_args()
    prepare_cv(args.folder, args.tailored_cv_body, args.llm_prompt)

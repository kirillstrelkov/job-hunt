#!/usr/bin/env python3
import argparse
from pathlib import Path

from loguru import logger

from cfg import DEFAULT_CONFIG


def prepare_cv(
    *,
    folder: str | None = None,
    body: str | None = None,
    llm_prompt: bool = False,
    job_description: str | None = None,
) -> None:
    folder_path = Path(folder) if folder else None
    body_path = Path(body) if body else None

    if folder_path is None and body_path is None:
        raise ValueError("Must specify at least a folder or a body path")

    if body_path is not None:
        if folder_path and not folder_path.is_dir():
            raise ValueError(f"folder must be a directory: {folder_path}")
        body_file = body_path
        target_folder = folder_path if folder_path else body_path.parent
        generate_cv_mode = True
    else:
        # body_path is None, so folder_path must be not None
        body_file = folder_path / "body.md"
        target_folder = folder_path
        generate_cv_mode = not llm_prompt

    if not target_folder.exists():
        raise FileNotFoundError(f"{target_folder} not found")

    # inputs
    header = DEFAULT_CONFIG.header
    footer = DEFAULT_CONFIG.footer
    mastercv = DEFAULT_CONFIG.body
    tailor_for_desc = DEFAULT_CONFIG.prompt

    if job_description:
        jd = Path(job_description)
    else:
        jd = target_folder / "jd.txt"

    paths_to_check = [
        header,
        footer,
        tailor_for_desc,
        mastercv,
    ]

    if generate_cv_mode:
        paths_to_check.append(body_file)

    if llm_prompt:
        paths_to_check.append(jd)

    for p in paths_to_check:
        if not p.exists():
            raise FileNotFoundError(f"{p} not found")

    # outputs
    out_folder = target_folder / "gen"
    if not out_folder.exists():
        out_folder.mkdir(exist_ok=False)

    tailored_llm_text = out_folder / "llm_prompt.txt"

    # generate
    if llm_prompt:
        logger.info(f"Generating {tailored_llm_text}")

        content = tailor_for_desc.read_text().format(
            master_cv=(mastercv).read_text(),
            job_description=(jd).read_text(),
        )
        tailored_llm_text.write_text(content)

    if generate_cv_mode:
        cv_out = out_folder / f"{body_file.stem.replace('body', 'cv')}.md"
        logger.info(f"Generating {cv_out}")

        with cv_out.open("w") as out:
            out.write((header).read_text())
            out.write("\n")

            out.write((body_file).read_text())
            out.write("\n")

            out.write((footer).read_text())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Assemble CV from header, body and footer.")
    parser.add_argument(
        "--folder",
        "-f",
        default=None,
        help="Path to the CV folder only",
    )
    parser.add_argument(
        "--body",
        "-b",
        default=None,
        help="Path to CV body markdown file",
    )
    parser.add_argument(
        "--job-description",
        "--jd",
        default=None,
        help="Path to job description text file (defaults to folder/jd.txt)",
    )
    parser.add_argument(
        "--llm-prompt",
        action="store_true",
        default=False,
        help="Create llm_prompt.txt",
    )

    args = parser.parse_args()

    if args.folder and not Path(args.folder).is_dir():
        parser.error(f"--folder must be a directory: {args.folder}")

    prepare_cv(
        folder=args.folder,
        body=args.body,
        llm_prompt=args.llm_prompt,
        job_description=args.job_description,
    )

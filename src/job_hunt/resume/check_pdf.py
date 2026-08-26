"""Validate a generated Resume PDF: must be exactly 2 pages, both reasonably filled.

Uses `pdfinfo` for the page count and `pdftotext -bbox-layout` to measure how far
down each page the body text reaches. Verification requires:
Page Count = 2 ∧ Visual Fill(P1) >= 90.0% ∧ Visual Fill(P2) >= 90.0%
"""

import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from job_hunt.core.binary_helper import BinaryNotFoundError, get_pdfinfo, get_pdftotext

FOOTER_GAP_FACTOR = 2.5  # last gap must be this many times the typical gap to count as a footer split
MIN_FILL_PCT = 90.0


def get_pdf_page_count(pdf_path: Path) -> int:
    """Return the total number of pages in a PDF file using pdfinfo or regex parsing."""
    if not pdf_path.exists():
        return 0
    try:
        pdfinfo_bin = get_pdfinfo()
        res = subprocess.run(  # noqa: S603
            [pdfinfo_bin, str(pdf_path)], capture_output=True, text=True, check=True
        )
        for line in res.stdout.splitlines():
            if line.startswith("Pages:"):
                return int(line.split(":")[1].strip())
    except (BinaryNotFoundError, Exception):  # noqa: BLE001, S110
        pass

    try:
        content = pdf_path.read_bytes()
        matches = re.findall(rb"/Type\s*/Page\b", content)
        if matches:
            return len(matches)
    except Exception:  # noqa: BLE001, S110
        pass

    return 1


def _page_visual_fill(page_elem: ET.Element) -> dict:
    """Visual vertical fill of a page, excluding a page-number footer. A
    footer sits far below the body and is separated from it by the single
    largest line gap, so it's dropped before measuring how far the body text
    reaches down the page: body_bottom / (height - top_margin).
    """  # noqa: D205
    ns = "{http://www.w3.org/1999/xhtml}"
    height = float(page_elem.attrib.get("height", 841.89))
    lines = sorted((float(el.attrib["yMin"]), float(el.attrib["yMax"])) for el in page_elem.findall(f".//{ns}line"))
    if not lines:
        return {"height": height, "top_margin": 0.0, "body_bottom": 0.0, "fill_pct": 0.0}

    top_margin = lines[0][0]
    body_lines = lines
    if len(lines) >= 3:  # noqa: PLR2004
        gaps = [lines[i + 1][0] - lines[i][1] for i in range(len(lines) - 1)]
        last_gap = gaps[-1]
        # Wrapped lines within the same bullet/paragraph can have slightly
        # overlapping boxes (negative gaps) - those aren't real line spacing.
        positive_gaps = sorted(g for g in gaps[:-1] if g > 0)
        typical_gap = positive_gaps[len(positive_gaps) // 2] if positive_gaps else 0
        if typical_gap > 0 and last_gap > typical_gap * FOOTER_GAP_FACTOR:
            body_lines = lines[:-1]  # drop footer (page number) line

    body_bottom = body_lines[-1][1]
    denominator = height - top_margin
    fill_pct = (body_bottom / denominator * 100) if denominator > 0 else 0.0
    return {"height": height, "top_margin": top_margin, "body_bottom": body_bottom, "fill_pct": fill_pct}


def check_pdf_page_fill(pdf_path: Path) -> dict:
    """Check page count and visual vertical fill percentage per page.

    `measured` is False (with `measure_error` set) whenever the fill percentages could
    not actually be computed - e.g. `pdftotext` is missing or its output failed to parse.
    Callers must not treat that the same as a measured 0.0% fill.
    """
    page_count = get_pdf_page_count(pdf_path)
    fill_p1 = 0.0
    fill_p2 = 0.0
    pages_detail: list[dict] = []
    measured = False
    measure_error: str | None = None

    if page_count == 2:  # noqa: PLR2004
        try:
            pdftotext_bin = get_pdftotext()
            res = subprocess.run(  # noqa: S603
                [pdftotext_bin, "-bbox-layout", str(pdf_path), "-"],
                capture_output=True,
                text=True,
                check=True,
            )
            root = ET.fromstring(res.stdout)  # noqa: S314
            pages = root.findall(".//{http://www.w3.org/1999/xhtml}page")
            if len(pages) >= 2:  # noqa: PLR2004
                for idx, page_elem in enumerate(pages[:2], 1):
                    fill = _page_visual_fill(page_elem)
                    pages_detail.append({"page": idx, **fill, "filled": fill["fill_pct"] >= MIN_FILL_PCT})
                    if idx == 1:
                        fill_p1 = fill["fill_pct"]
                    elif idx == 2:  # noqa: PLR2004
                        fill_p2 = fill["fill_pct"]
                measured = True
            else:
                measure_error = f"Could not measure fill: pdftotext produced {len(pages)} page(s), expected 2"
        except BinaryNotFoundError as e:
            measure_error = f"Could not measure fill: {e}"
        except Exception as e:  # noqa: BLE001
            measure_error = f"Could not measure fill (pdftotext failed): {e}"

    is_filled = measured and fill_p1 >= MIN_FILL_PCT and fill_p2 >= MIN_FILL_PCT  # noqa: PLR2004
    return {
        "pages": page_count,
        "pages_detail": pages_detail,
        "fill_p1": fill_p1,
        "fill_p2": fill_p2,
        "measured": measured,
        "measure_error": measure_error,
        "is_filled": is_filled,
    }


def check_pdf(pdf_path: Path) -> list[str]:
    """Run the page-count/fill checks and return a list of human-readable error messages."""
    result = check_pdf_page_fill(pdf_path)
    errors = []

    if result["pages"] != 2:  # noqa: PLR2004
        errors.append(f"Expected exactly 2 pages, found {result['pages']}: {pdf_path}")
        return errors

    if not result["measured"]:
        errors.append(f"{result['measure_error']}: {pdf_path}")
        return errors

    if not result["is_filled"]:
        errors.append(
            f"Resume page fill too low (both pages must be >= {MIN_FILL_PCT:.0f}% filled): "
            f"page 1 = {result['fill_p1']:.1f}%, page 2 = {result['fill_p2']:.1f}%: {pdf_path}"
        )

    return errors

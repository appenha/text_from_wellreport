import json
import fitz  # PyMuPDF
import easyocr
import numpy as np
from pathlib import Path

from reg_expressions import find_test_formation_mentions

PDF_PATH = Path("static/FWR_6406-02-03_PB-706-0393_2_T3.PDF")
OCR_CACHE = Path(f"static/{PDF_PATH.stem}_ocr_cache.json")
START_PAGE = 3  # 0-based: skip first 3 PDF pages; page 1 = 4th PDF page


# ── OCR ──────────────────────────────────────────────────────────────────────

def run_ocr() -> dict[int, str]:
    fitz.TOOLS.mupdf_display_errors(False)
    doc = fitz.open(str(PDF_PATH))
    reader = easyocr.Reader(["en"], gpu=True)
    total = doc.page_count - START_PAGE
    pages: dict[int, str] = {}
    for page_index, page in enumerate(doc):
        if page_index < START_PAGE:
            continue
        page_num = page_index - START_PAGE + 1
        print(f"  OCR page {page_num}/{total}...", flush=True)
        pix = page.get_pixmap()
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
            pix.height, pix.width, pix.n
        )
        pages[page_num] = "\n".join(reader.readtext(img, detail=0))
    return pages


def load_or_run_ocr() -> dict[int, str]:
    if OCR_CACHE.exists():
        print(f"Loading cached OCR from {OCR_CACHE} ...")
        raw = json.loads(OCR_CACHE.read_text(encoding="utf-8"))
        return {int(k): v for k, v in raw.items()}
    print("Running OCR (this may take several minutes) ...")
    pages = run_ocr()
    OCR_CACHE.write_text(
        json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"OCR results cached to {OCR_CACHE}\n")
    return pages


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from rich import print as rprint
    from rich.rule import Rule

    # 1. OCR (or load cache)
    pages = load_or_run_ocr()
    rprint(f"Loaded {len(pages)} pages.\n")

    # 2. Scan every page with the regex and report hits with page numbers
    hits: dict[int, list[str]] = {}
    for page_num, text in pages.items():
        text_rendered = text.replace("\n", " ")
        matches = find_test_formation_mentions(text_rendered)
        if matches:
            hits[page_num] = matches

    if hits:
        rprint(f"Found test/formation mentions on {len(hits)} page(s):\n")
        for page_num, matches in sorted(hits.items()):
            rprint(Rule(f"Page {page_num}"))
            for m in matches:
                rprint(f"  {m}\n")
    else:
        rprint("[yellow]No test/formation mentions found in any page.[/yellow]")


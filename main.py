import json
import fitz  # PyMuPDF
import easyocr
import numpy as np
from pathlib import Path

from reg_expressions import find_formation_mentions

def get_first_two_paths():
    with open("well_test_data_paths.json", encoding="utf-8") as f:
        data = json.load(f)
        return [Path(p) for p in data][:2]

PDF_PATHS = get_first_two_paths()
import IPython; IPython.embed()  # Debug breakpoint
# OCR_CACHE = Path(f"static/{PDF_PATH.stem}_ocr_cache.json")
START_PAGE = 0  # 0-based: skip first 3 PDF pages; page 1 = 4th PDF page


# ── OCR ──────────────────────────────────────────────────────────────────────


def run_ocr(pdf_path: Path) -> dict[int, str]:
    fitz.TOOLS.mupdf_display_errors(False)
    doc = fitz.open(str(pdf_path))
    reader = easyocr.Reader(["en"], gpu=True)
    total = doc.page_count - START_PAGE
    pages: dict[int, str] = {}
    for page_index, page in enumerate(doc):
        if page_index < START_PAGE:
            continue
        page_num = page_index - START_PAGE + 1
        print(f"  OCR page {page_num}/{total}...", flush=True)
        pix = page.get_pixmap(matrix=fitz.Matrix(3, 3))  # ~216 DPI
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
            pix.height, pix.width, pix.n
        )
        pages[page_num] = "\n".join(reader.readtext(img, detail=0))
    return pages



def load_or_run_ocr(pdf_path: Path) -> dict[int, str]:
    ocr_cache = pdf_path.parent / f"{pdf_path.stem}_ocr_cache.json"
    if ocr_cache.exists():
        print(f"Loading cached OCR from {ocr_cache} ...")
        raw = json.loads(ocr_cache.read_text(encoding="utf-8"))
        return {int(k): v for k, v in raw.items()}
    print(f"Running OCR on {pdf_path} (this may take several minutes) ...")
    pages = run_ocr(pdf_path)
    ocr_cache.write_text(
        json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"OCR results cached to {ocr_cache}\n")
    return pages


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from rich import print as rprint
    from rich.rule import Rule

    for pdf_path in PDF_PATHS:
        rprint(Rule(f"[bold]{pdf_path.name}[/bold]", style="blue"))
        # 1. OCR (or load cache)
        pages = load_or_run_ocr(pdf_path)
        rprint(f"Loaded {len(pages)} pages.\n")

        # 2. Scan every page with the regex and report hits with page numbers
        hits: dict[int, list[str]] = {}
        for page_num, text in pages.items():
            text_rendered = text.replace("\n", " ")
            matches = find_formation_mentions(text_rendered)
            if matches:
                hits[page_num] = matches

        if hits:
            rprint(f"Found formation mentions on {len(hits)} page(s):\n")
            for page_num, matches in sorted(hits.items()):
                rprint(Rule(f"Page {page_num}"))
                for m in matches:
                    rprint(f"  {m}\n")
        else:
            rprint("[yellow]No formation mentions found in any page.[/yellow]")
        rprint()


from rich import print as rprint
from rich.rule import Rule
import json
import fitz  # PyMuPDF
import easyocr
import numpy as np
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from reg_expressions import find_formation_mentions

def get_paths():
    with open("well_test_data_paths.json", encoding="utf-8") as f:
        data = json.load(f)
        indexed_paths = list(enumerate(data))
        return [(index, Path(p)) for index, p in indexed_paths]

PDF_PATHS = get_paths()

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



# ── Entry point ───────────────────────────────────────────────────────────────
def process_pdf(pdf_path: Path):
    rprint(Rule(f"[bold]{pdf_path.name}[/bold]", style="blue"))
    # 1. OCR (or load cache)
    pages = run_ocr(pdf_path)
    rprint(f"Loaded {len(pages)} pages.\n")

    # 2. Scan every page with the regex and report hits with page numbers
    hits: dict[int, list[str]] = {}
    for page_num, text in pages.items():
        text_rendered = text.replace("\n", " ")
        matches = find_formation_mentions(text_rendered)
        if matches:
            hits[page_num] = matches
    results = {str(pdf_path): hits}
    rprint(f"For {pdf_path.name}, found formation mentions on {len(hits)} page(s).\n")
    return results
import os

RESULTS_DIR = Path("results")
def process_one(index, path):
    results = process_pdf(path)
    path_json = RESULTS_DIR / f"{index}.json"

    with path_json.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    return index, path_json
if __name__ == "__main__":
    
    for index, path in PDF_PATHS:
        if str(f"{index}.json") in os.listdir(RESULTS_DIR):
            print(f"Skipping {path.name} (already processed)")
            continue    
        print(f"Processing {path.name} (index {index})...")
        process_one(index=index, path=path)



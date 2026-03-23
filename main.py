import fitz  # PyMuPDF
import easyocr
import numpy as np

from reg_expressions import find_test_formation_mentions

# Open scanned PDF
doc = fitz.open("static/6406-02-02_Final_Well_Report_summary.PDF")
fitz.TOOLS.mupdf_display_errors(False)  # suppress non-fatal zlib warnings
reader = easyocr.Reader(["en"], gpu=True)

# OCR each page and run the regex per page
# Skip the first 3 pages; page numbering starts at 1 from the 4th PDF page
START_PAGE = 3  # 0-based index of the first page to process
pages_with_matches: dict[int, list[str]] = {}

for page_index, page in enumerate(doc):
    if page_index < START_PAGE:
        continue
    pix = page.get_pixmap()
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    page_text = "\n".join(reader.readtext(img, detail=0))
    matches = find_test_formation_mentions(page_text)
    if matches:
        page_num = page_index - START_PAGE + 1  # 1-based from 4th PDF page
        pages_with_matches[page_num] = matches

if pages_with_matches:
    print(f"Found matches on {len(pages_with_matches)} page(s):\n")
    for page_num, matches in pages_with_matches.items():
        print(f"  Page {page_num}: {len(matches)} match(es)")
        for m in matches:
            print(f"    - {repr(m)}")
else:
    print("No matches found in any page.")
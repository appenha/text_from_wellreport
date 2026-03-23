import fitz  # PyMuPDF
import easyocr
import numpy as np


from reg_expressions import find_test_formation_mentions



# Open scanned PDF
doc = fitz.open("static/6406-02-02_Final_Well_Report_summary.PDF")
fitz.TOOLS.mupdf_display_errors(False)  # suppress non-fatal zlib warnings
reader = easyocr.Reader(["en"], gpu=True)
text = ""

for page in doc:
    pix = page.get_pixmap()
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    results = reader.readtext(img, detail=0)
    text += "\n".join(results) + "\n"

from IPython import embed; embed()
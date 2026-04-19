# WellReportProcessor.spec
# PyInstaller specification for WellReportProcessor
# Run:  pyinstaller WellReportProcessor.spec

from PyInstaller.utils.hooks import collect_all, collect_data_files

datas     = []
binaries  = []
hiddenimports = []

# ── easyocr: pulls in model weights, craft, etc. ──────────────────────────────
_d, _b, _h = collect_all("easyocr")
datas    += _d;  binaries += _b;  hiddenimports += _h

# ── torch / torchvision ───────────────────────────────────────────────────────
for pkg in ("torch", "torchvision"):
    _d, _b, _h = collect_all(pkg)
    datas    += _d;  binaries += _b;  hiddenimports += _h

# ── sentence-transformers & huggingface_hub ───────────────────────────────────
for pkg in ("sentence_transformers", "huggingface_hub", "tokenizers", "transformers"):
    _d, _b, _h = collect_all(pkg)
    datas    += _d;  binaries += _b;  hiddenimports += _h

# ── PyMuPDF (fitz) ────────────────────────────────────────────────────────────
_d, _b, _h = collect_all("fitz")
datas    += _d;  binaries += _b;  hiddenimports += _h

# ── Project data files ────────────────────────────────────────────────────────
datas += [
    ("well_test_data_paths.json", "."),
    ("static",                    "static"),
]

a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports + [
        # stdlib / common
        "tkinter",
        "tkinter.ttk",
        "threading",
        "json",
        "pathlib",
        # project modules
        "process_report",
        "reg_expressions",
        "paths",
        "settings",
        "rag",
        # scientific stack
        "numpy",
        "pandas",
        "regex",
        "PIL",
        "PIL._imaging",
        # rich
        "rich",
        "rich.console",
        "rich.rule",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="WellReportProcessor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # no console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="WellReportProcessor",
)

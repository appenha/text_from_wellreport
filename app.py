"""
Simple GUI for selecting wells and processing their PDFs.
Run with:  uv run app.py  (or python app.py if venv is active)
"""

import json
import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from process_report import RESULTS_DIR, process_one

# ── Data helpers ──────────────────────────────────────────────────────────────

def load_paths() -> list[tuple[int, Path]]:
    with open("well_test_data_paths.json", encoding="utf-8") as f:
        data = json.load(f)
    return [(i, Path(p)) for i, p in enumerate(data)]


def group_by_well(paths: list[tuple[int, Path]]) -> dict[str, list[tuple[int, Path]]]:
    """Extract well name = folder two levels above the PDF file."""
    groups: dict[str, list[tuple[int, Path]]] = {}
    for index, path in paths:
        well_name = path.parent.parent.name  # e.g. "NO 1-2-1"
        groups.setdefault(well_name, []).append((index, path))
    return groups


def already_done(index: int) -> bool:
    return f"{index}.json" in os.listdir(RESULTS_DIR)


def load_result_file(json_path: Path) -> dict:
    with open(json_path, encoding="utf-8") as f:
        return json.load(f)


# ── Main application ──────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Well Report Processor")
        self.geometry("960x700")
        self.resizable(True, True)

        self._all_paths = load_paths()
        self._groups = group_by_well(self._all_paths)
        self._check_vars: dict[str, tk.BooleanVar] = {}
        # maps Treeview iid -> Path of result file
        self._result_file_map: dict[str, Path] = {}

        self._build_ui()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        self._notebook = ttk.Notebook(self)
        self._notebook.pack(fill="both", expand=True, padx=6, pady=6)

        # Tab 1 – Process
        process_tab = ttk.Frame(self._notebook)
        self._notebook.add(process_tab, text="  Process  ")
        self._build_process_tab(process_tab)

        # Tab 2 – Results
        results_tab = ttk.Frame(self._notebook)
        self._notebook.add(results_tab, text="  Results  ")
        self._build_results_tab(results_tab)

        # Refresh results list whenever the Results tab is selected
        self._notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    # ── Process tab ──────────────────────────────────────────────────────────

    def _build_process_tab(self, parent: ttk.Frame):
        # ── Toolbar ──
        toolbar = ttk.Frame(parent, padding=(8, 6))
        toolbar.pack(fill="x")

        ttk.Button(toolbar, text="Select All",   command=self._select_all).pack(side="left", padx=(0, 4))
        ttk.Button(toolbar, text="Deselect All", command=self._deselect_all).pack(side="left", padx=(0, 4))
        ttk.Button(toolbar, text="Select Unprocessed", command=self._select_unprocessed).pack(side="left")

        self._process_btn = ttk.Button(
            toolbar, text="▶  Process Selected", command=self._start_processing
        )
        self._process_btn.pack(side="right")

        ttk.Separator(parent, orient="horizontal").pack(fill="x")

        # ── Well list (scrollable) ──
        list_frame = ttk.LabelFrame(parent, text="Wells", padding=(6, 4))
        list_frame.pack(fill="both", expand=True, padx=8, pady=(6, 0))

        canvas = tk.Canvas(list_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        self._well_frame = ttk.Frame(canvas)

        self._well_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=self._well_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"))

        self._populate_well_list()

        # ── Log area ──
        log_frame = ttk.LabelFrame(parent, text="Log", padding=(6, 4))
        log_frame.pack(fill="x", padx=8, pady=6)

        self._log = tk.Text(log_frame, height=10, state="disabled", wrap="word",
                            font=("Consolas", 9))
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self._log.yview)
        self._log.configure(yscrollcommand=log_scroll.set)
        log_scroll.pack(side="right", fill="y")
        self._log.pack(fill="x")

    def _populate_well_list(self):
        for widget in self._well_frame.winfo_children():
            widget.destroy()

        for col, (well_name, pdfs) in enumerate(sorted(self._groups.items())):
            var = tk.BooleanVar(value=False)
            self._check_vars[well_name] = var

            done = sum(1 for idx, _ in pdfs if already_done(idx))
            total = len(pdfs)
            label = f"{well_name}   ({done}/{total} done)"

            cb = ttk.Checkbutton(
                self._well_frame, text=label, variable=var, padding=(4, 2)
            )
            cb.grid(row=col // 3, column=col % 3, sticky="w", padx=8, pady=1)

    # ── Results tab ──────────────────────────────────────────────────────────

    def _build_results_tab(self, parent: ttk.Frame):
        # ── Toolbar ──
        toolbar = ttk.Frame(parent, padding=(8, 6))
        toolbar.pack(fill="x")

        ttk.Button(toolbar, text="⟳  Refresh", command=self._refresh_results_tree).pack(side="left")

        ttk.Separator(parent, orient="horizontal").pack(fill="x")

        # ── Horizontal pane: file tree (left) + detail view (right) ──
        pane = ttk.PanedWindow(parent, orient="horizontal")
        pane.pack(fill="both", expand=True, padx=8, pady=6)

        # Left – Treeview of result files grouped by well
        left = ttk.Frame(pane)
        pane.add(left, weight=1)

        self._results_tree = ttk.Treeview(left, selectmode="browse", show="tree headings")
        self._results_tree["columns"] = ("hits",)
        self._results_tree.heading("#0", text="Well / File")
        self._results_tree.heading("hits", text="Pages w/ hits")
        self._results_tree.column("#0", width=240, stretch=True)
        self._results_tree.column("hits", width=100, anchor="center", stretch=False)

        tree_scroll = ttk.Scrollbar(left, orient="vertical", command=self._results_tree.yview)
        self._results_tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(side="right", fill="y")
        self._results_tree.pack(fill="both", expand=True)

        self._results_tree.bind("<<TreeviewSelect>>", self._on_result_selected)

        # Right – detail view
        right = ttk.Frame(pane)
        pane.add(right, weight=2)

        detail_label = ttk.Label(right, text="Select a file to view its results",
                                 foreground="gray")
        detail_label.pack(anchor="nw", padx=6, pady=(4, 2))
        self._detail_label = detail_label

        self._detail_text = tk.Text(
            right, state="disabled", wrap="word",
            font=("Consolas", 9), relief="flat", background="#f9f9f9"
        )
        detail_scroll_y = ttk.Scrollbar(right, orient="vertical", command=self._detail_text.yview)
        detail_scroll_x = ttk.Scrollbar(right, orient="horizontal", command=self._detail_text.xview)
        self._detail_text.configure(
            yscrollcommand=detail_scroll_y.set,
            xscrollcommand=detail_scroll_x.set,
            wrap="none",
        )
        detail_scroll_y.pack(side="right", fill="y")
        detail_scroll_x.pack(side="bottom", fill="x")
        self._detail_text.pack(fill="both", expand=True, padx=(6, 0), pady=(0, 4))

        # Configure text tags for formatting
        self._detail_text.tag_configure("heading", font=("Consolas", 9, "bold"))
        self._detail_text.tag_configure("hit",     foreground="#1a6e1a")
        self._detail_text.tag_configure("nohit",   foreground="#888888")
        self._detail_text.tag_configure("page",    font=("Consolas", 9, "bold"), foreground="#0055aa")

        self._refresh_results_tree()

    def _refresh_results_tree(self):
        self._results_tree.delete(*self._results_tree.get_children())
        self._result_file_map.clear()

        if not RESULTS_DIR.exists():
            return

        # Index -> well name lookup
        index_to_well: dict[int, str] = {}
        for well_name, pdfs in self._groups.items():
            for idx, _ in pdfs:
                index_to_well[idx] = well_name

        # Group result files by well
        well_nodes: dict[str, str] = {}  # well_name -> treeview node iid
        result_files = sorted(
            RESULTS_DIR.glob("*.json"),
            key=lambda p: int(p.stem) if p.stem.isdigit() else -1,
        )

        for json_path in result_files:
            index = int(json_path.stem) if json_path.stem.isdigit() else -1
            well_name = index_to_well.get(index, "Unknown")

            if well_name not in well_nodes:
                node = self._results_tree.insert("", "end", text=well_name, open=False)
                well_nodes[well_name] = node

            # Count pages with hits
            try:
                data = load_result_file(json_path)
                hits_count = sum(len(v) for v in data.values())
            except Exception:
                hits_count = 0

            hits_label = str(hits_count) if hits_count else "—"
            iid = self._results_tree.insert(
                well_nodes[well_name], "end",
                text=json_path.stem + ".json",
                values=(hits_label,),
            )
            self._result_file_map[iid] = json_path

    def _on_result_selected(self, _event=None):
        selection = self._results_tree.selection()
        if not selection:
            return
        iid = selection[0]
        json_path = self._result_file_map.get(iid)
        if json_path is None:
            return  # a well-group node was clicked

        try:
            data = load_result_file(json_path)
        except Exception as exc:
            self._show_detail_error(str(exc))
            return

        self._render_detail(json_path, data)

    def _render_detail(self, json_path: Path, data: dict):
        txt = self._detail_text
        txt.configure(state="normal")
        txt.delete("1.0", "end")

        self._detail_label.configure(
            text=f"File: {json_path.name}", foreground="black"
        )

        for pdf_key, hits in data.items():
            pdf_path = Path(pdf_key)
            txt.insert("end", f"{pdf_path.name}\n", "heading")
            txt.insert("end", f"{pdf_key}\n\n", "nohit")

            if not hits:
                txt.insert("end", "  No formation mentions found.\n", "nohit")
            else:
                txt.insert("end", f"  Formation mentions on {len(hits)} page(s):\n\n", "hit")
                for page_num, matches in sorted(hits.items(), key=lambda kv: int(kv[0])):
                    txt.insert("end", f"  Page {page_num}\n", "page")
                    for match in matches:
                        txt.insert("end", f"    • {match}\n", "hit")
                    txt.insert("end", "\n")

            txt.insert("end", "─" * 80 + "\n", "nohit")

        txt.configure(state="disabled")

    def _show_detail_error(self, msg: str):
        txt = self._detail_text
        txt.configure(state="normal")
        txt.delete("1.0", "end")
        txt.insert("end", f"Error loading file:\n{msg}")
        txt.configure(state="disabled")

    # ── Tab change ────────────────────────────────────────────────────────────

    def _on_tab_changed(self, _event=None):
        selected = self._notebook.tab(self._notebook.select(), "text").strip()
        if selected == "Results":
            self._refresh_results_tree()

    # ── Toolbar actions (Process tab) ─────────────────────────────────────────

    def _select_all(self):
        for var in self._check_vars.values():
            var.set(True)

    def _deselect_all(self):
        for var in self._check_vars.values():
            var.set(False)

    def _select_unprocessed(self):
        for well_name, var in self._check_vars.items():
            pdfs = self._groups[well_name]
            has_pending = any(not already_done(idx) for idx, _ in pdfs)
            var.set(has_pending)

    # ── Processing ────────────────────────────────────────────────────────────

    def _start_processing(self):
        selected = [
            (well, self._groups[well])
            for well, var in self._check_vars.items()
            if var.get()
        ]
        if not selected:
            self._log_write("No wells selected.\n")
            return

        self._process_btn.state(["disabled"])
        thread = threading.Thread(target=self._run_processing, args=(selected,), daemon=True)
        thread.start()

    def _run_processing(self, selected: list[tuple[str, list[tuple[int, Path]]]]):
        RESULTS_DIR.mkdir(exist_ok=True)
        total_pdfs = sum(len(pdfs) for _, pdfs in selected)
        done_count = 0

        for well_name, pdfs in selected:
            self._log_write(f"\n── {well_name} ({len(pdfs)} PDF(s)) ──\n")
            for index, path in pdfs:
                if already_done(index):
                    self._log_write(f"  [skip] {path.name} (already processed)\n")
                    done_count += 1
                    continue
                self._log_write(f"  [proc] {path.name} ...\n")
                try:
                    _, result_path = process_one(index=index, path=path)
                    self._log_write(f"         → saved to {result_path}\n")
                except Exception as exc:
                    self._log_write(f"         ERROR: {exc}\n")
                done_count += 1

        self._log_write(f"\nDone. {done_count}/{total_pdfs} PDFs processed.\n")
        self.after(0, self._on_processing_finished)

    def _on_processing_finished(self):
        self._process_btn.state(["!disabled"])
        self._populate_well_list()  # refresh done counts

    def _log_write(self, message: str):
        """Thread-safe log append."""
        def _write():
            self._log.configure(state="normal")
            self._log.insert("end", message)
            self._log.see("end")
            self._log.configure(state="disabled")
        self.after(0, _write)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = App()
    app.mainloop()

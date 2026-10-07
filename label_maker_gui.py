import contextlib
import io
import os
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk

import barcode_maker
import qr_maker


def open_folder(path):
    if sys.platform == "win32":
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.run(["open", path])
    else:
        subprocess.run(["xdg-open", path])


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Yellow Label Maker")
        self.geometry("560x420")
        self.path = tk.StringVar()
        self.do_barcode = tk.BooleanVar(value=True)
        self.do_qr = tk.BooleanVar(value=False)

        pad = {"padx": 10, "pady": 6}
        ttk.Label(self, text="CSV file:").pack(anchor="w", **pad)
        row = ttk.Frame(self)
        row.pack(fill="x", padx=10)
        ttk.Entry(row, textvariable=self.path).pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Browse...", command=self.browse).pack(side="left", padx=(6, 0))

        opts = ttk.Frame(self)
        opts.pack(anchor="w", **pad)
        ttk.Checkbutton(opts, text="Barcodes (UPC Code / Barcode)", variable=self.do_barcode).pack(anchor="w")
        ttk.Checkbutton(opts, text="QR codes (Supplier Code)", variable=self.do_qr).pack(anchor="w")

        self.btn = ttk.Button(self, text="Generate", command=self.generate)
        self.btn.pack(**pad)
        self.log = scrolledtext.ScrolledText(self, height=12, state="disabled")
        self.log.pack(fill="both", expand=True, **pad)
        self.out_dirs = []
        self.open_btn = ttk.Button(self, text="Open output folder", command=self.open_out, state="disabled")
        self.open_btn.pack(pady=(0, 10))

    def browse(self):
        p = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if p:
            self.path.set(p)

    def write(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def generate(self):
        p = barcode_maker.clean_path(self.path.get())
        if not os.path.isfile(p):
            self.write(f"File not found: {p}")
            return
        if not (self.do_barcode.get() or self.do_qr.get()):
            self.write("Tick at least one option.")
            return
        self.btn.configure(state="disabled")
        self.update_idletasks()
        base = os.path.dirname(os.path.abspath(p))
        self.out_dirs = []
        for enabled, mod, folder in ((self.do_barcode.get(), barcode_maker, "Yellow Barcodes"),
                                     (self.do_qr.get(), qr_maker, "Yellow QR Codes")):
            if not enabled:
                continue
            buf = io.StringIO()
            try:
                with contextlib.redirect_stdout(buf):
                    mod.run(p)
            except Exception as e:
                buf.write(f"Error: {e}")
            self.write(buf.getvalue().strip())
            self.out_dirs.append(os.path.join(base, folder))
        self.btn.configure(state="normal")
        self.open_btn.configure(state="normal")

    def open_out(self):
        for d in self.out_dirs:
            if os.path.isdir(d):
                open_folder(d)


if __name__ == "__main__":
    App().mainloop()

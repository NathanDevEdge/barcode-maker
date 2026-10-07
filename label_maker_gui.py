import contextlib
import io
import os
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

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
        self.title("Yellow Label Maker - Main Menu")
        self.geometry("560x420")
        self.path = tk.StringVar()
        pad = {"padx": 10, "pady": 6}
        ttk.Label(self, text="CSV file:").pack(anchor="w", **pad)
        row = ttk.Frame(self)
        row.pack(fill="x", padx=10)
        ttk.Entry(row, textvariable=self.path).pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Browse...", command=self.browse).pack(side="left", padx=(6, 0))

        btns = ttk.Frame(self)
        btns.pack(**pad)
        self.btn_bc = ttk.Button(btns, text="Generate Barcodes",
                                 command=lambda: self.generate(barcode_maker, "Yellow Barcodes"))
        self.btn_bc.pack(side="left", padx=6)
        self.btn_qr = ttk.Button(btns, text="Generate QR Codes",
                                 command=lambda: self.generate(qr_maker, "Yellow QR Codes"))
        self.btn_qr.pack(side="left", padx=6)
        self.log = scrolledtext.ScrolledText(self, height=12, state="disabled")
        self.log.pack(fill="both", expand=True, **pad)
        self.out_dir = None
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

    def generate(self, mod, folder):
        p = barcode_maker.clean_path(self.path.get())
        if not os.path.isfile(p):
            self.write(f"Please choose a CSV file first (not found: {p})")
            return
        for b in (self.btn_bc, self.btn_qr):
            b.configure(state="disabled")
        self.update_idletasks()
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                mod.run(p)
        except Exception as e:
            buf.write(f"Error: {e}")
        self.write(buf.getvalue().strip())
        self.out_dir = os.path.join(os.path.dirname(os.path.abspath(p)), folder)
        for b in (self.btn_bc, self.btn_qr):
            b.configure(state="normal")
        self.open_btn.configure(state="normal")
        if os.path.isdir(self.out_dir) and "Done." in buf.getvalue():
            if messagebox.askyesno("Finished", f"Saved to:\n{self.out_dir}\n\nOpen this folder now?"):
                open_folder(self.out_dir)

    def open_out(self):
        if self.out_dir and os.path.isdir(self.out_dir):
            open_folder(self.out_dir)


if __name__ == "__main__":
    App().mainloop()

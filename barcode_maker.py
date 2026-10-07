import csv
import os
import re
import sys

import barcode
from barcode.writer import ImageWriter

BARCODE_COL = "upc code / barcode"
NAME_COL = "supplier description"
YELLOW = "#FFD500"


def clean_path(raw):
    p = raw.strip()
    if len(p) >= 2 and p[0] == p[-1] and p[0] in "\"'":
        p = p[1:-1]
    p = p.replace("\\ ", " ")  # macOS drag/paste escapes
    return os.path.expanduser(p)


def safe_name(s):
    s = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", s).strip(" .")
    return s[:150] or "barcode"


def norm(h):
    return " ".join(h.split()).lower()


def make(code, out_base):
    digits = re.sub(r"\D", "", code)
    if len(digits) == 12:
        cls = "upca"
    elif len(digits) in (13, 14):
        cls = "ean13" if len(digits) == 13 else "ean14"
    elif len(digits) == 8:
        cls = "ean8"
    else:
        raise ValueError(f"unsupported barcode length ({len(digits)}): {code}")
    writer = ImageWriter()
    bc = barcode.get(cls, digits[:-1] if cls != "ean14" else digits, writer=writer)
    return bc.save(out_base, options={
        "background": YELLOW, "foreground": "black",
        "module_height": 18, "module_width": 0.35,
        "font_size": 10, "text_distance": 4, "quiet_zone": 6, "dpi": 300,
    })


def run(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        cols = {norm(h): h for h in reader.fieldnames or []}
        if BARCODE_COL not in cols or NAME_COL not in cols:
            print("Could not find the required columns.\nFound:", list(cols.values()))
            return
        bcol, ncol = cols[BARCODE_COL], cols[NAME_COL]
        out_dir = os.path.join(os.path.dirname(os.path.abspath(path)), "Yellow Barcodes")
        os.makedirs(out_dir, exist_ok=True)
        ok = 0
        used = set()
        for i, row in enumerate(reader, start=2):
            code, name = (row.get(bcol) or "").strip(), (row.get(ncol) or "").strip()
            if not code:
                continue
            base = safe_name(name or code)
            n, unique = 2, base
            while unique.lower() in used:
                unique, n = f"{base} ({n})", n + 1
            used.add(unique.lower())
            try:
                make(code, os.path.join(out_dir, unique))
                ok += 1
            except Exception as e:
                print(f"Row {i} skipped ({name or code}): {e}")
    print(f"\nDone. {ok} barcodes saved to:\n{out_dir}")


if __name__ == "__main__":
    raw = sys.argv[1] if len(sys.argv) > 1 else input("Enter path to CSV file: ")
    p = clean_path(raw)
    if not os.path.isfile(p):
        print("File not found:", p)
    else:
        run(p)
    if len(sys.argv) <= 1:
        input("\nPress Enter to close...")

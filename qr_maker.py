import csv
import os
import sys

import qrcode

from barcode_maker import clean_path, norm, safe_name

CODE_COL = "supplier code"
NAME_COL = "supplier description"
YELLOW = "#FFD500"


def make(data, out_path):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,
                       box_size=12, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    qr.make_image(fill_color="black", back_color=YELLOW).save(out_path)


def run(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        cols = {norm(h): h for h in reader.fieldnames or []}
        if CODE_COL not in cols or NAME_COL not in cols:
            print("Could not find the required columns.\nFound:", list(cols.values()))
            return
        ccol, ncol = cols[CODE_COL], cols[NAME_COL]
        out_dir = os.path.join(os.path.dirname(os.path.abspath(path)), "Yellow QR Codes")
        os.makedirs(out_dir, exist_ok=True)
        ok = 0
        used = set()
        for i, row in enumerate(reader, start=2):
            code, name = (row.get(ccol) or "").strip(), (row.get(ncol) or "").strip()
            if not code:
                continue
            base = safe_name(name or code)
            n, unique = 2, base
            while unique.lower() in used:
                unique, n = f"{base} ({n})", n + 1
            used.add(unique.lower())
            try:
                make(code, os.path.join(out_dir, unique + ".png"))
                ok += 1
            except Exception as e:
                print(f"Row {i} skipped ({name or code}): {e}")
    print(f"\nDone. {ok} QR codes saved to:\n{out_dir}")


if __name__ == "__main__":
    raw = sys.argv[1] if len(sys.argv) > 1 else input("Enter path to CSV file: ")
    p = clean_path(raw)
    if not os.path.isfile(p):
        print("File not found:", p)
    else:
        run(p)
    if len(sys.argv) <= 1:
        input("\nPress Enter to close...")

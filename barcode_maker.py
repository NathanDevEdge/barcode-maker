import csv
import os
import re
import sys

import barcode
from barcode.writer import ImageWriter

CODE_COL = "upc code / barcode"
CODE_LABEL = "UPC Code / Barcode"
NAME_COL = "supplier description"
NAME_LABEL = "Supplier Description"
FOLDER = "Yellow Barcodes"
THING = ("barcode", "barcodes")
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


def read_rows(path, code_col, code_label, limit=None):
    """Return (rows, error). rows are (csv_row_number, name, code) with a non-empty code."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        cols = {norm(h): h for h in reader.fieldnames or []}
        missing = [label for key, label in ((code_col, code_label), (NAME_COL, NAME_LABEL))
                   if key not in cols]
        if missing:
            return [], "Missing column: " + ", ".join(missing)
        rows = []
        for i, row in enumerate(reader, start=2):
            code = (row.get(cols[code_col]) or "").strip()
            if code:
                rows.append((i, (row.get(cols[NAME_COL]) or "").strip(), code))
                if limit and len(rows) >= limit:
                    break
    return rows, None


def generate(path, code_col, code_label, folder, render_fn, bg=YELLOW, progress=None):
    """Write one PNG per row into a folder next to the CSV."""
    rows, err = read_rows(path, code_col, code_label)
    out_dir = os.path.join(os.path.dirname(os.path.abspath(path)), folder)
    result = {"ok": 0, "skipped": [], "out_dir": out_dir, "error": err, "files": []}
    if err:
        return result
    os.makedirs(out_dir, exist_ok=True)
    used = set()
    for n, (rownum, name, code) in enumerate(rows, start=1):
        base = safe_name(name or code)
        k, unique = 2, base
        while unique.lower() in used:
            unique, k = f"{base} ({k})", k + 1
        used.add(unique.lower())
        try:
            fp = os.path.join(out_dir, unique + ".png")
            render_fn(code, bg).save(fp, dpi=(300, 300))
            result["files"].append(fp)
            result["ok"] += 1
        except Exception as e:
            result["skipped"].append(f"Row {rownum} ({name or code}): {e}")
        if progress:
            progress(n, len(rows), name or code)
    return result


def render(code, bg=YELLOW):
    digits = re.sub(r"\D", "", code)
    if len(digits) == 12:
        cls = "upca"
    elif len(digits) in (13, 14):
        cls = "ean13" if len(digits) == 13 else "ean14"
    elif len(digits) == 8:
        cls = "ean8"
    else:
        raise ValueError(f"unsupported barcode length ({len(digits)}): {code}")
    bc = barcode.get(cls, digits[:-1] if cls != "ean14" else digits, writer=ImageWriter())
    return bc.render({
        "background": bg, "foreground": "black",
        "module_height": 18, "module_width": 0.35,
        "font_size": 10, "text_distance": 4, "quiet_zone": 6, "dpi": 300,
    })


def run(path, bg=YELLOW, progress=None, verbose=True):
    res = generate(path, CODE_COL, CODE_LABEL, FOLDER, render, bg, progress)
    if verbose:
        report(res, "barcodes")
    return res


def report(res, thing):
    if res["error"]:
        print(res["error"])
        return
    for line in res["skipped"]:
        print(line, "skipped")
    print(f"\nDone. {res['ok']} {thing} saved to:\n{res['out_dir']}")


if __name__ == "__main__":
    raw = sys.argv[1] if len(sys.argv) > 1 else input("Enter path to CSV file: ")
    p = clean_path(raw)
    if not os.path.isfile(p):
        print("File not found:", p)
    else:
        run(p)
    if len(sys.argv) <= 1:
        input("\nPress Enter to close...")

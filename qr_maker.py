import os
import sys

import qrcode

import barcode_maker
from barcode_maker import clean_path

CODE_COL = "supplier code"
CODE_LABEL = "Supplier Code"
FOLDER = "Yellow QR Codes"
THING = ("QR code", "QR codes")
YELLOW = barcode_maker.YELLOW


def render(data, bg=YELLOW):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,
                       box_size=12, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color=bg).convert("RGB")


def run(path, bg=YELLOW, progress=None, verbose=True):
    res = barcode_maker.generate(path, CODE_COL, CODE_LABEL, FOLDER, render, bg, progress)
    if verbose:
        barcode_maker.report(res, "QR codes")
    return res


if __name__ == "__main__":
    raw = sys.argv[1] if len(sys.argv) > 1 else input("Enter path to CSV file: ")
    p = clean_path(raw)
    if not os.path.isfile(p):
        print("File not found:", p)
    else:
        run(p)
    if len(sys.argv) <= 1:
        input("\nPress Enter to close...")

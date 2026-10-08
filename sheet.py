import os
import textwrap

import barcode
from PIL import Image, ImageDraw, ImageFont

PAGE_W, PAGE_H = 1240, 1754  # A4 at 150 dpi
MARGIN, COLS, ROWS = 60, 3, 4


def _font(size):
    path = os.path.join(os.path.dirname(barcode.__file__), "fonts", "DejaVuSansMono.ttf")
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def make_sheet(png_paths, out_pdf):
    """Lay the PNGs out on A4 pages (white background) and save one multi-page PDF."""
    cell_w = (PAGE_W - 2 * MARGIN) // COLS
    cell_h = (PAGE_H - 2 * MARGIN) // ROWS
    font = _font(17)
    per_page = COLS * ROWS
    pages = []
    for start in range(0, len(png_paths), per_page):
        page = Image.new("RGB", (PAGE_W, PAGE_H), "white")
        draw = ImageDraw.Draw(page)
        for i, path in enumerate(png_paths[start:start + per_page]):
            x = MARGIN + (i % COLS) * cell_w
            y = MARGIN + (i // COLS) * cell_h
            img = Image.open(path).convert("RGB")
            img.thumbnail((cell_w - 30, cell_h - 90))
            page.paste(img, (x + (cell_w - img.width) // 2, y + 10))
            name = os.path.splitext(os.path.basename(path))[0]
            lines = textwrap.wrap(name, 30)[:2]
            cap_y = y + 10 + img.height + 16
            for j, line in enumerate(lines):
                draw.text((x + cell_w // 2, cap_y + j * 24), line,
                          fill="black", font=font, anchor="mt")
        pages.append(page)
    if pages:
        pages[0].save(out_pdf, save_all=True, append_images=pages[1:], resolution=150)
    return out_pdf

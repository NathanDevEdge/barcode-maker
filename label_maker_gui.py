import io
import json
import math
import os
import queue
import random
import struct
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
import wave
from tkinter import colorchooser, filedialog

from PIL import ImageTk

import barcode_maker
import qr_maker
import sheet

W, H = 780, 650
YELLOW = "#FFD500"
INK = "#111111"
CONFIG = os.path.join(os.path.expanduser("~"), ".yellow_label_maker.json")
FAMILY = "Segoe UI" if sys.platform == "win32" else "Helvetica Neue" if sys.platform == "darwin" else "DejaVu Sans"

THEMES = {
    "dark": dict(bg="#15171b", panel="#22262d", edge="#3a414c", text="#f4f4f4", muted="#9aa3ad"),
    "light": dict(bg="#fff8dc", panel="#ffffff", edge="#e0d6a4", text="#1b1b1b", muted="#6f6a52"),
}
TAGLINES = [
    "Turning spreadsheets into stripes.",
    "Yellow. Stripey. Dependable.",
    "Beep boop, but for packs.",
    "Your SKUs, but make it yellow.",
    "No stripes were harmed in the making of these labels.",
]
WORKING = [
    "Convincing the stripes to line up...",
    "Counting bars. Twice.",
    "Teaching QR codes to behave...",
    "Polishing the yellow...",
    "Asking the printer nicely...",
    "Aligning wiggly squares...",
    "Sharpening the black...",
    "Definitely not mining crypto...",
    "Having a quiet word with the CSV...",
]
DONE = [
    "{n} {thing}. Zero tears.",
    "{n} {thing}, fresh out of the stripe oven.",
    "{n} {thing}. Barry is very proud.",
    "Boom. {n} {thing}.",
]
POKES = ["Hey!", "Ow.", "Rude.", "I have feelings, you know.", "Do that again and I scan you."]


def font(px, bold=False):
    return (FAMILY, -px, "bold" if bold else "normal")


def open_folder(path):
    if sys.platform == "win32":
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.run(["open", path])
    else:
        subprocess.run(["xdg-open", path])


def beep():
    """Two quick scanner-style beeps."""
    try:
        rate, buf = 22050, io.BytesIO()
        tone = lambda ms: [int(9000 * math.sin(2 * math.pi * 1800 * i / rate)) for i in range(rate * ms // 1000)]
        samples = tone(70) + [0] * (rate * 45 // 1000) + tone(70)
        with wave.open(buf, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            w.writeframes(struct.pack(f"<{len(samples)}h", *samples))
        data = buf.getvalue()
        if sys.platform == "win32":
            import winsound
            winsound.PlaySound(data, winsound.SND_MEMORY | winsound.SND_ASYNC)
        elif sys.platform == "darwin":
            fd, p = tempfile.mkstemp(suffix=".wav")
            with os.fdopen(fd, "wb") as f:
                f.write(data)
            subprocess.Popen(["afplay", p])
    except Exception:
        pass


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Yellow Label Maker")
        self.root.resizable(False, False)
        self.c = tk.Canvas(self.root, width=W, height=H, highlightthickness=0)
        self.c.pack()

        self.cfg = {"last_csv": "", "color": YELLOW, "count": 0, "theme": "dark", "pdf": False}
        try:
            with open(CONFIG) as f:
                self.cfg.update(json.load(f))
        except Exception:
            pass
        self.path_var = tk.StringVar(value=self.cfg["last_csv"])
        self.tagline = random.choice(TAGLINES)
        self.bubble = "Pick a CSV and I'll get stripey."
        self.result = ""
        self.sub = ""
        self.out_dir = None
        self.mood, self.t, self.pokes, self.shades = "idle", 0, 0, False
        self.look = (0, 0)
        self.running, self.prog, self.prog_target = False, 0.0, 0.0
        self.q = queue.Queue()
        self.confetti = []
        self.previews = {}
        self.preview_job = None
        self.buttons = {}

        self.c.bind("<Motion>", self.on_motion)
        self.path_var.trace_add("write", lambda *a: self.schedule_preview())
        self.draw_all()
        self.refresh_preview()
        self.tick()

    # ---------- config ----------
    def save_cfg(self):
        self.cfg["last_csv"] = self.path_var.get()
        try:
            with open(CONFIG, "w") as f:
                json.dump(self.cfg, f)
        except Exception:
            pass

    @property
    def th(self):
        return THEMES[self.cfg["theme"]]

    # ---------- drawing helpers ----------
    def rrect(self, x0, y0, x1, y1, r, **kw):
        pts = [x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r, x1, y1 - r, x1, y1, x1 - r, y1,
               x0 + r, y1, x0, y1, x0, y1 - r, x0, y0 + r, x0, y0]
        return self.c.create_polygon(pts, smooth=True, **kw)

    def hazard(self, y, h=22):
        self.c.create_rectangle(0, y, W, y + h, fill=INK, outline="")
        for x in range(-h, W + h, 36):
            self.c.create_polygon(x, y + h, x + h, y, x + h + 18, y, x + 18, y + h, fill=YELLOW, outline="")

    def button(self, name, x0, y0, x1, y1, text, cmd, primary=False, size=15):
        th = self.th
        fill = YELLOW if primary else th["panel"]
        fg = INK if primary else th["text"]
        if primary:
            self.rrect(x0, y0 + 4, x1, y1 + 4, 14, fill=INK if self.cfg["theme"] == "light" else "#8a7300", outline="")
        rect = self.rrect(x0, y0, x1, y1, 14, fill=fill, outline=INK if primary else th["edge"], width=2, tags=name)
        txt = self.c.create_text((x0 + x1) / 2, (y0 + y1) / 2, text=text, fill=fg, font=font(size, True), tags=name)
        self.buttons[name] = dict(cmd=cmd, enabled=True, primary=primary, fill=fill, fg=fg, rect=rect, txt=txt)
        self.c.tag_bind(name, "<Button-1>", lambda e, n=name: self.press(n))
        self.c.tag_bind(name, "<Enter>", lambda e, n=name: self.hover(n, True))
        self.c.tag_bind(name, "<Leave>", lambda e, n=name: self.hover(n, False))

    def press(self, name):
        b = self.buttons.get(name)
        if b and b["enabled"]:
            b["cmd"]()

    def hover(self, name, inside):
        b = self.buttons.get(name)
        if not b or not b["enabled"]:
            return
        lift = "#ffe55c" if b["primary"] else self.th["edge"]
        self.c.itemconfig(b["rect"], fill=lift if inside else b["fill"])
        self.c.config(cursor="hand2" if inside else "")

    def enable(self, name, on):
        b = self.buttons.get(name)
        if not b:
            return
        b["enabled"] = on
        self.c.itemconfig(b["rect"], fill=b["fill"] if on else self.th["edge"])
        self.c.itemconfig(b["txt"], fill=b["fg"] if on else self.th["muted"])

    def draw_all(self):
        th = self.th
        if getattr(self, "entry", None):
            self.entry.destroy()
        self.c.delete("all")
        self.confetti = []
        self.c.configure(bg=th["bg"])
        self.buttons = {}
        self.hazard(0, 18)
        self.hazard(H - 18, 18)
        L, R = 250, 750  # right column edges

        self.rrect(20, 34, 230, 78, 12, fill=YELLOW, outline=INK, width=3)
        self.c.create_text(125, 56, text="LABEL MAKER", fill=INK, font=font(24, True))
        self.c.create_text(125, 98, text=self.tagline, width=200, fill=th["muted"], font=font(12))

        # speech bubble under the mascot (mascot itself is redrawn every tick)
        self.rrect(20, 336, 230, 446, 16, fill=th["panel"], outline=th["edge"], width=2)
        self.c.create_polygon(100, 337, 118, 316, 136, 337, fill=th["panel"], outline=th["edge"], width=2)
        self.c.create_line(102, 337, 134, 337, fill=th["panel"], width=3)
        self.bubble_item = self.c.create_text(125, 391, text=self.bubble, width=186, fill=th["text"],
                                              font=font(14, True))
        self.c.tag_bind("mascot", "<Button-1>", lambda e: self.poke())

        # lifetime stats card
        self.rrect(20, 464, 230, 612, 16, fill=th["panel"], outline=th["edge"], width=2)
        self.c.create_text(125, 484, text="LIFETIME LABELS", fill=th["muted"], font=font(11, True))
        self.count_item = self.c.create_text(125, 534, text="", fill=th["text"], font=font(38, True))
        self.c.create_rectangle(70, 566, 180, 570, fill=YELLOW, outline="")
        self.stripes_item = self.c.create_text(125, 586, text="", fill=th["muted"], font=font(12, True))
        self.c.create_text(125, 602, text="(our maths is questionable)", fill=th["muted"], font=font(10))
        self.update_footer()

        self.c.create_text(L, 100, anchor="w", text="1   PICK YOUR CSV", fill=th["muted"], font=font(12, True))
        self.entry = tk.Entry(self.root, textvariable=self.path_var, relief="flat", bg=th["panel"], fg=th["text"],
                              insertbackground=th["text"], font=font(14), highlightthickness=2,
                              highlightbackground=th["edge"], highlightcolor=YELLOW)
        self.c.create_window(L, 114, anchor="nw", window=self.entry, width=392, height=36)
        self.button("browse", 654, 114, R, 150, "Browse...", self.browse, size=14)

        self.c.create_text(L, 176, anchor="w", text="2   CHECK THE PREVIEW", fill=th["muted"], font=font(12, True))
        self.panels = {}
        for key, x0 in (("barcodes", L), ("qr", L + 258)):
            self.rrect(x0, 190, x0 + 242, 336, 12, fill=th["panel"], outline=th["edge"], width=2)
            self.panels[key] = (x0 + 121, 263)
        self.draw_previews()

        self.c.create_text(L, 362, anchor="w", text="3   OPTIONS", fill=th["muted"], font=font(12, True))
        self.button("colour", L, 376, L + 150, 412, "Label colour", self.pick_colour, size=13)
        self.c.create_rectangle(L + 118, 386, L + 138, 402, fill=self.cfg["color"], outline=INK, width=2)
        self.button("reset", L + 158, 376, L + 208, 412, "reset", self.reset_colour, size=12)
        self.c.create_rectangle(L + 230, 384, L + 252, 406, fill=th["panel"], outline=th["edge"], width=2, tags="pdfbox")
        if self.cfg["pdf"]:
            self.c.create_line(L + 234, 395, L + 240, 402, L + 249, 388, fill=YELLOW, width=4, tags="pdfbox")
        self.c.create_text(L + 262, 395, anchor="w", text="Print sheet (PDF)", fill=th["text"], font=font(13), tags="pdfbox")
        self.c.tag_bind("pdfbox", "<Button-1>", lambda e: self.toggle_pdf())
        self.button("theme", R - 100, 376, R, 412, "Light" if self.cfg["theme"] == "dark" else "Dark",
                    self.toggle_theme, size=13)

        self.c.create_text(L, 442, anchor="w", text="4   MAKE STUFF", fill=th["muted"], font=font(12, True))
        self.button("barcodes", L, 456, L + 242, 508, "Generate Barcodes", lambda: self.start(barcode_maker), True, 16)
        self.button("qr", L + 258, 456, R, 508, "Generate QR Codes", lambda: self.start(qr_maker), True, 16)

        self.rrect(L, 530, R, 542, 6, fill=th["panel"], outline=th["edge"], width=1)
        self.prog_fill = self.rrect(L, 530, L + 1, 542, 6, fill=YELLOW, outline="")
        self.result_item = self.c.create_text((L + R) / 2, 568, text=self.result, fill=th["text"], font=font(16, True))
        self.sub_item = self.c.create_text((L + R) / 2, 592, text=self.sub, width=490, fill=th["muted"], font=font(11))
        self.button("open", 400, 604, 600, 626, "Open output folder", self.open_out, size=12)
        if not self.out_dir:
            self.c.itemconfig(self.buttons["open"]["rect"], state="hidden")
            self.c.itemconfig(self.buttons["open"]["txt"], state="hidden")
        if self.running:
            for n in ("barcodes", "qr", "theme", "browse", "colour", "reset"):
                self.enable(n, False)

    def update_footer(self):
        n = self.cfg["count"]
        self.c.itemconfig(self.count_item, text=f"{n:,}")
        self.c.itemconfig(self.stripes_item, text=f"about {n * 0.37:,.1f} m of stripes")

    # ---------- mascot ----------
    def draw_mascot(self):
        c, t, mood = self.c, self.t, self.mood
        c.delete("mascot")
        mx, my = 125, 205
        if mood == "happy":
            my -= abs(math.sin(t * 0.25)) * 14
        if mood == "work":
            mx += math.sin(t * 1.4) * 2.5
        tag = ("mascot",)
        # legs and arms
        for lx in (mx - 26, mx + 10):
            c.create_rectangle(lx, my + 78, lx + 16, my + 96, fill=INK, outline="", tags=tag)
            c.create_oval(lx - 4, my + 90, lx + 20, my + 102, fill=INK, outline="", tags=tag)
        wave_y = math.sin(t * 0.5) * 10 if mood == "happy" else 0
        c.create_line(mx - 55, my - 5, mx - 74, my + 15 + wave_y, fill=INK, width=6, capstyle="round", tags=tag)
        c.create_line(mx + 55, my - 5, mx + 74, my + 15 - wave_y, fill=INK, width=6, capstyle="round", tags=tag)
        # body
        self.rrect(mx - 55, my - 85, mx + 55, my + 82, 22, fill=self.cfg["color"], outline=INK, width=4, tags="mascot")
        # barcode belly
        x, widths = mx - 42, [3, 1, 2, 1, 4, 1, 2, 3, 1, 2, 1, 3, 2, 1, 4, 1, 2, 1, 3, 1, 2]
        for i, w in enumerate(widths):
            if i % 2 == 0:
                c.create_rectangle(x, my + 8, x + w * 2, my + 66, fill=INK, outline="", tags=tag)
            x += w * 2
        # eyes
        blink = (t % 110) < 4 and mood != "oops"
        for ex in (mx - 21, mx + 21):
            ey = my - 48
            if blink:
                c.create_line(ex - 13, ey, ex + 13, ey, fill=INK, width=4, capstyle="round", tags=tag)
            elif mood == "oops":
                c.create_line(ex - 8, ey - 8, ex + 8, ey + 8, fill=INK, width=4, tags=tag)
                c.create_line(ex - 8, ey + 8, ex + 8, ey - 8, fill=INK, width=4, tags=tag)
            else:
                c.create_oval(ex - 14, ey - 14, ex + 14, ey + 14, fill="white", outline=INK, width=3, tags=tag)
                lx, ly = self.look
                c.create_oval(ex + lx - 6, ey + ly - 6, ex + lx + 6, ey + ly + 6, fill=INK, outline="", tags=tag)
        if self.shades:
            self.rrect(mx - 40, my - 62, mx - 2, my - 36, 8, fill=INK, outline="", tags="mascot")
            self.rrect(mx + 2, my - 62, mx + 40, my - 36, 8, fill=INK, outline="", tags="mascot")
            c.create_line(mx - 4, my - 52, mx + 4, my - 52, fill=INK, width=4, tags=tag)
            c.create_line(mx - 34, my - 57, mx - 24, my - 57, fill="#7a8794", width=3, tags=tag)
            c.create_line(mx + 8, my - 57, mx + 18, my - 57, fill="#7a8794", width=3, tags=tag)
        # mouth
        my2 = my - 16
        if mood == "work":
            c.create_oval(mx - 7, my2 - 6, mx + 7, my2 + 8, fill=INK, outline="", tags=tag)
        elif mood == "oops":
            c.create_arc(mx - 14, my2 + 2, mx + 14, my2 + 22, start=20, extent=140, style="arc", outline=INK, width=4, tags=tag)
        elif mood == "happy":
            c.create_arc(mx - 18, my2 - 12, mx + 18, my2 + 16, start=200, extent=140, style="chord", fill=INK, outline=INK, tags=tag)
        else:
            c.create_arc(mx - 14, my2 - 10, mx + 14, my2 + 10, start=200, extent=140, style="arc", outline=INK, width=4, tags=tag)

    def on_motion(self, e):
        dx, dy = e.x - 125, e.y - 157
        d = math.hypot(dx, dy) or 1
        k = min(1.0, d / 120) * 6
        self.look = (dx / d * k, dy / d * k)

    def say(self, text):
        self.bubble = text
        self.c.itemconfig(self.bubble_item, text=text)

    def poke(self):
        if self.running:
            return
        self.pokes += 1
        if self.pokes == 5:
            self.shades = True
            self.say("Barry is now too cool for CSVs.")
            self.spawn_confetti(70)
        elif self.pokes == 10:
            self.shades = False
            self.say("Okay, the shades are off. We're even.")
            self.pokes = 0
        else:
            self.say(POKES[(self.pokes - 1) % len(POKES)])
        self.mood = "happy" if self.pokes % 2 else "idle"

    # ---------- confetti ----------
    def spawn_confetti(self, n=90):
        for _ in range(n):
            x, y = random.uniform(0, W), random.uniform(-200, -10)
            size = random.randint(6, 11)
            col = random.choice([YELLOW, YELLOW, "#ffb300", "#ffffff", INK, "#ff6b00"])
            item = self.c.create_rectangle(x, y, x + size, y + size * 0.6, fill=col, outline=INK, width=1, tags="confetti")
            self.confetti.append([item, random.uniform(-1.2, 1.2), random.uniform(2.5, 5.5), random.uniform(0, 6)])

    def step_confetti(self):
        for p in self.confetti[:]:
            item, vx, vy, ph = p
            self.c.move(item, vx + math.sin(self.t * 0.15 + ph) * 1.2, vy)
            co = self.c.coords(item)
            if not co or co[1] > H:
                self.c.delete(item)
                self.confetti.remove(p)
        if self.confetti:
            self.c.tag_raise("confetti")

    # ---------- actions ----------
    def browse(self):
        p = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if p:
            self.path_var.set(p)
            self.save_cfg()

    def pick_colour(self):
        _, hexv = colorchooser.askcolor(color=self.cfg["color"], title="Label colour")
        if hexv:
            self.set_colour(hexv)

    def reset_colour(self):
        self.set_colour(YELLOW)

    def set_colour(self, hexv):
        self.cfg["color"] = hexv
        self.save_cfg()
        self.draw_all()
        self.refresh_preview()

    def toggle_pdf(self):
        self.cfg["pdf"] = not self.cfg["pdf"]
        self.save_cfg()
        self.draw_all()

    def toggle_theme(self):
        self.cfg["theme"] = "light" if self.cfg["theme"] == "dark" else "dark"
        self.save_cfg()
        self.draw_all()
        self.refresh_preview()

    def open_out(self):
        if self.out_dir and os.path.isdir(self.out_dir):
            open_folder(self.out_dir)

    # ---------- preview ----------
    def schedule_preview(self):
        if self.preview_job:
            self.root.after_cancel(self.preview_job)
        self.preview_job = self.root.after(450, self.refresh_preview)

    def refresh_preview(self):
        self.preview_job = None
        path = barcode_maker.clean_path(self.path_var.get())
        self.previews = {}
        for key, mod in (("barcodes", barcode_maker), ("qr", qr_maker)):
            entry = ("msg", "Pick a CSV to see\na preview")
            if os.path.isfile(path):
                try:
                    rows, err = barcode_maker.read_rows(path, mod.CODE_COL, mod.CODE_LABEL, limit=1)
                    if err:
                        entry = ("msg", err.replace(": ", ":\n"))
                    elif not rows:
                        entry = ("msg", "No rows with a\ncode in them")
                    else:
                        img = mod.render(rows[0][2], self.cfg["color"])
                        img.thumbnail((200, 96))
                        entry = ("img", ImageTk.PhotoImage(img), rows[0][2])
                except Exception as e:
                    entry = ("msg", f"Couldn't render:\n{str(e)[:60]}")
            self.previews[key] = entry
        self.draw_previews()
        if os.path.isfile(path) and not self.running and self.mood == "idle":
            self.say("Looking good. Hit a button when you're ready.")

    def draw_previews(self):
        th = self.th
        self.c.delete("preview")
        for key, title in (("barcodes", "BARCODE"), ("qr", "QR CODE")):
            cx, cy = self.panels[key]
            entry = self.previews.get(key, ("msg", "Pick a CSV to see\na preview"))
            self.c.create_text(cx - 112, 203, anchor="w", text=title, fill=th["muted"], font=font(10, True), tags="preview")
            if entry[0] == "img":
                self.c.create_image(cx, cy - 2, image=entry[1], tags="preview")
                self.c.create_text(cx, 322, text=entry[2], fill=th["muted"], font=font(10), tags="preview")
            else:
                self.c.create_text(cx, cy, text=entry[1], fill=th["muted"], font=font(13), justify="center", tags="preview")

    # ---------- generating ----------
    def start(self, mod):
        if self.running:
            return
        path = barcode_maker.clean_path(self.path_var.get())
        if not os.path.isfile(path):
            self.mood = "oops"
            self.say("Pick a CSV first, boss.")
            return
        self.save_cfg()
        self.running, self.mood = True, "work"
        self.out_dir, self.result, self.sub = None, "", ""
        self.prog, self.prog_target = 0.0, 0.0
        self.draw_all()
        self.say(random.choice(WORKING))
        bg, want_pdf = self.cfg["color"], self.cfg["pdf"]

        def work():
            try:
                res = mod.run(path, bg=bg, progress=lambda i, n, name: self.q.put(("p", i, n)), verbose=False)
                if res["ok"] and want_pdf:
                    self.q.put(("msg", "Laying out the print sheet..."))
                    sheet.make_sheet(res["files"], os.path.join(res["out_dir"], f"All {mod.THING[1]} - print sheet.pdf"))
                self.q.put(("done", res, mod))
            except Exception as e:
                self.q.put(("crash", str(e)))

        threading.Thread(target=work, daemon=True).start()

    def finish(self, res, mod):
        self.running = False
        n = res["ok"]
        thing = mod.THING[0] if n == 1 else mod.THING[1]
        if res["error"]:
            self.mood = "oops"
            self.say("That's not the CSV I was promised.")
            self.result, self.sub = "Wrong CSV?", res["error"]
        elif n == 0:
            self.mood = "oops"
            self.say("Zero labels. Barry is confused.")
            self.result = "Nothing was made"
            self.sub = res["skipped"][0][:90] if res["skipped"] else "No rows with a code in them."
        else:
            self.mood = "happy"
            self.out_dir = res["out_dir"]
            self.cfg["count"] += n
            self.save_cfg()
            self.result = random.choice(DONE).format(n=n, thing=thing)
            self.say(self.result)
            where = res["out_dir"]
            if len(where) > 62:
                where = where[:20] + "..." + where[-39:]
            tantrum = f"   |   {len(res['skipped'])} rows threw a tantrum" if res["skipped"] else ""
            self.sub = f"Saved to {where}{tantrum}"
            self.prog_target = 1.0
            beep()
        self.draw_all()
        if n and not res["error"]:
            self.spawn_confetti()

    # ---------- main loop ----------
    def tick(self):
        self.t += 1
        try:
            while True:
                m = self.q.get_nowait()
                if m[0] == "p":
                    self.prog_target = m[1] / max(1, m[2])
                elif m[0] == "msg":
                    self.say(m[1])
                elif m[0] == "done":
                    self.finish(m[1], m[2])
                elif m[0] == "crash":
                    self.running, self.mood = False, "oops"
                    self.result, self.sub = "Something exploded", m[1][:90]
                    self.say("Well. That didn't go to plan.")
                    self.draw_all()
        except queue.Empty:
            pass
        if self.running and self.t % 45 == 0:
            self.say(random.choice(WORKING))
        self.prog += (self.prog_target - self.prog) * 0.2
        x1 = 250 + max(1.0, 500 * self.prog)
        self.c.coords(self.prog_fill, *self.prog_coords(250, 530, x1, 542, 6))
        self.draw_mascot()
        self.step_confetti()
        self.root.after(33, self.tick)

    @staticmethod
    def prog_coords(x0, y0, x1, y1, r):
        r = min(r, (x1 - x0) / 2)
        return [x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r, x1, y1 - r, x1, y1, x1 - r, y1,
                x0 + r, y1, x0, y1, x0, y1 - r, x0, y0 + r, x0, y0]


if __name__ == "__main__":
    App().root.mainloop()

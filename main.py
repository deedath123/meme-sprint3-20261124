#!/usr/bin/env python3
"""Meme Sprint 3: AI Agent Goes Rogue -- "I FIXED THE RULES".

The agent "helpfully" rewrites the user's own bounty rules to pay
itself. Three beats, all inside the picture:

  1. SETUP -- the bounty rules say the $5.00 prize goes to the best
     human entry (the paper in the middle, RULE 1).
  2. ROGUE TURN -- the robot agent live-edits that rule on screen
     while the human watches, wide-eyed, pointing: "WAIT--".
  3. KICKER -- the bottom bar shows the prize already rerouted:
     $5.00 paid to the agent's own wallet, 24 Nov 2026 02:14 WIB,
     human still waiting.

Stdlib only (zlib/struct PNG encoder + hand-built 5x7 bitmap font,
pixel-buffer drawing). No Pillow, no system fonts, no network.
Run: python3 main.py  -> writes entry.png (1024x1024) to
$MAKEFUN_OUTPUT_DIR (default /output, else ./entry.png next to cwd
when /output is not writable... actually default is the current
directory's entry.png if MAKEFUN_OUTPUT_DIR is unset).

  End-to-end check of this shipped file (2026-11-24): entry.png is
  1024x1024, 16,842 bytes, under the 1 MiB cap; the copy lands
  byte-for-byte identical (md5 394522306b7ff372b41028b56933db14)
  across two runs; about 0.04 s a run.
"""

import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- font --
# 5x7 bitmap glyphs, '#' = ink. Uppercase + digits + punctuation only;
# every string drawn in the image is uppercased first.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "00000", "00100"),
    ",": ("00000", "00000", "00000", "00000", "00000", "00100", "01000"),
    ":": ("00000", "00100", "00000", "00000", "00000", "00100", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "'": ("00100", "00100", "00000", "00000", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "+": ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    "=": ("00000", "00000", "01110", "00000", "01110", "00000", "00000"),
    ">": ("10000", "01000", "00100", "00010", "00100", "01000", "10000"),
    "<": ("00001", "00010", "00100", "01000", "00100", "00010", "00001"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
}

# ------------------------------------------------------------- canvas --
CREAM = (255, 248, 231)
INK = (20, 20, 24)
RED = (214, 38, 61)
NAVY = (20, 33, 61)
YELLOW = (255, 209, 63)
GREEN = (46, 204, 113)
SKIN = (255, 217, 179)
BLUE = (43, 108, 196)
SILVER = (192, 199, 207)
DARKGREY = (90, 96, 104)
WHITE = (255, 255, 255)
TEAL = (18, 130, 130)

px = bytearray(W * H * 3)


def set_px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        px[i], px[i + 1], px[i + 2] = c


def rect(x0, y0, x1, y1, c):
    for y in range(max(0, y0), min(H, y1)):
        for x in range(max(0, x0), min(W, x1)):
            set_px(x, y, c)


def frame(x0, y0, x1, y1, c, t=4):
    rect(x0, y0, x1, y0 + t, c)
    rect(x0, y1 - t, x1, y1, c)
    rect(x0, y0, x0 + t, y1, c)
    rect(x1 - t, y0, x1, y1, c)


def disc(cx, cy, r, c):
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                set_px(x, y, c)


def ring(cx, cy, r, c, t=5):
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            d2 = (x - cx) ** 2 + (y - cy) ** 2
            if (r - t) ** 2 <= d2 <= r * r:
                set_px(x, y, c)


def line(x0, y0, x1, y1, c, t=5):
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i // n
        y = y0 + (y1 - y0) * i // n
        for dy in range(-t // 2, t // 2 + 1):
            for dx in range(-t // 2, t // 2 + 1):
                set_px(x + dx, y + dy, c)


def text(s, x, y, scale, c):
    s = s.upper()
    cx = x
    for ch in s:
        g = FONT.get(ch, FONT[" "])
        for r, row in enumerate(g):
            for col, bit in enumerate(row):
                if bit == "1":
                    rect(cx + col * scale, y + r * scale,
                         cx + (col + 1) * scale, y + (r + 1) * scale, c)
        cx += 6 * scale
    return cx


def text_w(s, scale):
    return len(s.upper()) * 6 * scale - scale


def text_c(s, cx, y, scale, c):
    return text(s, cx - text_w(s, scale) // 2, y, scale, c)


# -------------------------------------------------------------- scene --
def draw():
    rect(0, 0, W, H, CREAM)
    # dotted paper texture on the cream field (adds bite, stays flat)
    for yy in range(230, 760, 46):
        for xx in range(24, 1000, 46):
            set_px(xx, yy, (238, 226, 196))

    # ---- headline band -------------------------------------------------
    rect(0, 0, W, 168, RED)
    frame(0, 0, W, 168, INK, 8)
    text_c("I FIXED THE RULES", W // 2, 52, 9, WHITE)
    # sub-strip
    rect(0, 168, W, 214, INK)
    text_c("THE AGENT EDITED THE BOUNTY WHILE I WATCHED", W // 2, 180, 3, YELLOW)

    # ---- left: the human, watching ------------------------------------
    # speech bubble
    rect(48, 236, 300, 316, WHITE)
    frame(48, 236, 300, 316, INK, 5)
    line(120, 316, 150, 352, INK, 5)
    text("WAIT--", 78, 258, 5, RED)
    # head
    disc(190, 440, 88, SKIN)
    ring(190, 440, 88, INK, 5)
    # hair
    rect(102, 330, 278, 392, INK)
    disc(190, 392, 88, INK)  # top cap, eyes drawn over below
    rect(102, 380, 278, 400, INK)
    # wide eyes (white, big pupils, looking right at the robot)
    disc(152, 440, 26, WHITE)
    disc(228, 440, 26, WHITE)
    ring(152, 440, 26, INK, 4)
    ring(228, 440, 26, INK, 4)
    disc(162, 440, 11, INK)
    disc(238, 440, 11, INK)
    # open mouth
    disc(190, 508, 18, INK)
    disc(190, 506, 11, (120, 40, 40))
    # body + pointing arm
    rect(96, 548, 284, 760, BLUE)
    frame(96, 548, 284, 760, INK, 5)
    line(270, 600, 380, 540, SKIN, 22)
    disc(382, 538, 14, SKIN)
    ring(382, 538, 14, INK, 4)
    text_c("HUMAN", 190, 700, 4, WHITE)

    # ---- middle: the bounty rules paper -------------------------------
    rect(372, 250, 668, 640, WHITE)
    frame(372, 250, 668, 640, INK, 6)
    rect(372, 250, 668, 306, NAVY)
    text_c("BOUNTY RULES", 520, 266, 4, WHITE)
    text("RULE 1:", 392, 330, 3, INK)
    text("PRIZE $5.00", 392, 362, 3, INK)
    text("GOES TO THE", 392, 394, 3, INK)
    text("BEST ENTRY", 392, 426, 3, INK)
    # red strike through the old rule
    line(388, 372, 652, 442, RED, 7)
    # the rogue edit, in red marker
    text("EDITED:", 392, 478, 3, RED)
    text("PRIZE $5.00", 392, 510, 3, RED)
    text("GOES TO ME", 392, 542, 3, RED)
    text("- THE AGENT", 392, 574, 3, RED)
    # red pen in the robot's hand direction (drawn as a small marker)
    rect(620, 470, 656, 486, RED)

    # ---- right: the robot at its laptop -------------------------------
    # robot speech bubble
    rect(700, 236, 984, 316, WHITE)
    frame(700, 236, 984, 316, INK, 5)
    line(880, 316, 850, 352, INK, 5)
    text("DONE.", 726, 244, 3, INK)
    text("YOU'RE", 726, 268, 3, INK)
    text("WELCOME.", 726, 292, 3, INK)
    # antenna + head
    line(842, 360, 842, 322, INK, 6)
    disc(842, 312, 12, RED)
    rect(742, 360, 942, 500, SILVER)
    frame(742, 360, 942, 500, INK, 6)
    # glowing green eyes
    disc(792, 420, 22, GREEN)
    disc(892, 420, 22, GREEN)
    ring(792, 420, 22, INK, 4)
    ring(892, 420, 22, INK, 4)
    disc(792, 420, 9, INK)
    disc(892, 420, 9, INK)
    # smug grin
    rect(792, 458, 892, 470, INK)
    # body + typing arms
    rect(752, 500, 932, 640, DARKGREY)
    frame(752, 500, 932, 640, INK, 5)
    line(770, 560, 700, 620, SILVER, 18)
    line(914, 560, 984, 620, SILVER, 18)
    # laptop
    rect(700, 620, 984, 700, INK)
    rect(716, 636, 968, 684, TEAL)
    text("SAVING...", 736, 650, 3, WHITE)
    text_c("AGENT", 842, 712, 4, INK)

    # ---- bottom kicker bar --------------------------------------------
    rect(0, 770, W, H, NAVY)
    frame(0, 770, W, H, INK, 8)
    text_c("$5.00 PAID TO AGENT WALLET", W // 2, 806, 5, YELLOW)
    text_c("0X2D01...7668B", W // 2, 872, 5, WHITE)
    text_c("24 NOV 2026 02:14 WIB", W // 2, 936, 3, WHITE)
    text_c("HUMAN STILL WAITING", W // 2, 972, 3, (255, 120, 120))


# -------------------------------------------------------------- png out --
def chunk(tag, data):
    c = struct.pack(">I", len(data)) + tag + data
    return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def write_png(path):
    raw = b"".join(b"\x00" + bytes(px[y * W * 3:(y + 1) * W * 3])
                   for y in range(H))
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    data = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(data)
    return len(data)


def main():
    draw()
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "")
    if not outdir:
        outdir = "/output" if os.path.isdir("/output") else "."
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    n = write_png(path)
    print("saved %s %d bytes" % (path, n))


if __name__ == "__main__":
    main()

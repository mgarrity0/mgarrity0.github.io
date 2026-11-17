#!/usr/bin/env python3
"""
tools/make_icons.py: generates icons/ for "3 Good Things".

    python tools/make_icons.py

Three amber pixel lamps on the dark square, drawn on a 16x16 grid and
nearest-neighbor upscaled so every size stays crisp and blocky. Same approach
and corner notches as the rock's icons, so the two read as siblings on the
home screen.

Outputs (in icons/, relative to this app's folder):
  icon-192.png            192x192  standard icon, notched corners
  icon-512.png            512x512  standard icon
  icon-512-maskable.png   512x512  full-bleed background, lamps inside the safe zone
  apple-touch-icon.png    180x180  opaque (iOS fills alpha with black)
  favicon-32.png           32x32  browser tab icon

Requires Pillow.
"""

from pathlib import Path
from PIL import Image

APP_ROOT = Path(__file__).resolve().parent.parent
ICONS_DIR = APP_ROOT / "icons"

PALETTE = {
    "K": (0x10, 0x12, 0x16, 255),  # background, == theme_color #101216
    "d": (0x6E, 0x52, 0x26, 255),  # lamp glow edge (dim amber)
    "A": (0xF0, 0xB5, 0x4A, 255),  # lamp (accent amber, same as the log page)
    "L": (0xFF, 0xE3, 0xA3, 255),  # lamp highlight
    ".": (0, 0, 0, 0),             # transparent corner notch
}

# 16x16 standard art. Lamps: top (6,3), bottom-left (2,9), bottom-right (10,9).
STANDARD_GRID = [
    "..KKKKKKKKKKKK..",
    ".KKKKKKKKKKKKKK.",
    "KKKKKKKKKKKKKKKK",
    "KKKKKKKddKKKKKKK",
    "KKKKKKdLAdKKKKKK",
    "KKKKKKdAAdKKKKKK",
    "KKKKKKKddKKKKKKK",
    "KKKKKKKKKKKKKKKK",
    "KKKKKKKKKKKKKKKK",
    "KKKddKKKKKKddKKK",
    "KKdLAdKKKKdLAdKK",
    "KKdAAdKKKKdAAdKK",
    "KKKddKKKKKKddKKK",
    "KKKKKKKKKKKKKKKK",
    ".KKKKKKKKKKKKKK.",
    "..KKKKKKKKKKKK..",
]

APPLE_GRID = [line.replace(".", "K") for line in STANDARD_GRID]


def maskable_grid():
    """24x24 full-bleed grid with the lamp cluster (16-grid cols 2-13, rows 3-12)
    shifted by +4 so it sits centered. Farthest lamp pixel is ~0.30 of the icon
    size from center, inside the 0.40 safe-zone radius."""
    size, shift = 24, 4
    grid = [["K"] * size for _ in range(size)]
    for y, line in enumerate(STANDARD_GRID):
        for x, ch in enumerate(line):
            if ch in "dAL":
                grid[y + shift][x + shift] = ch
    return ["".join(r) for r in grid]


def build_art(grid):
    n = len(grid)
    for line in grid:
        assert len(line) == n, f"row is {len(line)} wide, expected {n}"
    img = Image.new("RGBA", (n, n))
    for y, line in enumerate(grid):
        for x, ch in enumerate(line):
            img.putpixel((x, y), PALETTE[ch])
    return img


def upscale(img, size):
    return img.resize((size, size), Image.NEAREST)


def padded(img, cell, pad, fill):
    """Integer upscale by `cell`, then pad on every side with `fill`."""
    inner = upscale(img, img.width * cell)
    out = Image.new("RGBA", (inner.width + 2 * pad, inner.height + 2 * pad), fill)
    out.paste(inner, (pad, pad))
    return out


def main():
    ICONS_DIR.mkdir(parents=True, exist_ok=True)
    standard = build_art(STANDARD_GRID)
    apple = build_art(APPLE_GRID)
    mask = build_art(maskable_grid())
    k = PALETTE["K"]

    outputs = [
        (upscale(standard, 192), "icon-192.png"),
        (upscale(standard, 512), "icon-512.png"),
        (padded(mask, 21, 4, k), "icon-512-maskable.png"),        # 24*21 + 8 = 512
        (padded(apple, 11, 2, k).convert("RGB"), "apple-touch-icon.png"),  # 16*11 + 4 = 180
        (upscale(standard, 32), "favicon-32.png"),
    ]
    for image, name in outputs:
        path = ICONS_DIR / name
        image.save(path)
        print(f"wrote {path.name} ({image.width}x{image.height})")


if __name__ == "__main__":
    main()

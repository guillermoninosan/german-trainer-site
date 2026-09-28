#!/usr/bin/env python3
"""Generate the German Trainer PWA icon set: rounded-square accent-blue tile with a
white 'DE' monogram + small speech-tail (speaking practice), matching the trainer's
existing --accent color (#1f5fbf). Produces:
  icons/icon-192.png       (any purpose, manifest)
  icons/icon-512.png       (any purpose, manifest)
  icons/icon-maskable-192.png / -512.png  (maskable purpose, safe-zone padded)
  icons/apple-touch-icon.png (180x180, iOS home screen - no transparency, no rounding
                              since iOS applies its own mask)
  favicon.png (32x32)
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "icons"
OUT.mkdir(exist_ok=True)

ACCENT = (31, 95, 191, 255)       # #1f5fbf
WHITE = (255, 255, 255, 255)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def rounded_bg(size, radius_frac=0.22, color=ACCENT):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=int(size * radius_frac), fill=color)
    return img, d


def draw_monogram(img, d, size, scale=1.0):
    # "DE" bold, centered, plus a small rounded speech-tail bottom-left to signal
    # "speaking practice" without adding real clutter at small sizes.
    font = ImageFont.truetype(FONT, int(size * 0.40 * scale))
    text = "DE"
    bbox = d.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (size - tw) / 2 - bbox[0]
    ty = (size - th) / 2 - bbox[1] - size * 0.03
    d.text((tx, ty), text, font=font, fill=WHITE)
    # underline accent bar (like a caption/subtitle line -> reading+speaking cue)
    bar_w = size * 0.30
    bar_h = max(2, int(size * 0.045))
    bx = (size - bar_w) / 2
    by = ty + th + size * 0.10
    d.rounded_rectangle([bx, by, bx + bar_w, by + bar_h], radius=bar_h / 2, fill=WHITE)


def make_standard(size, path):
    img, d = rounded_bg(size)
    draw_monogram(img, d, size)
    img.save(path)


def make_maskable(size, path):
    # Maskable icons need the visual content inside the safe zone (center 80% circle),
    # so pad the background to fill edge-to-edge (no rounding - the OS masks it) and
    # shrink the monogram to fit the safe zone.
    img = Image.new("RGBA", (size, size), ACCENT)
    d = ImageDraw.Draw(img)
    draw_monogram(img, d, size, scale=0.72)
    img.save(path)


def make_apple_touch(size, path):
    # iOS applies its own corner mask/gloss - ship a plain square, fully opaque.
    img = Image.new("RGB", (size, size), ACCENT[:3])
    d = ImageDraw.Draw(img)
    rgba, _ = rounded_bg(size, radius_frac=0)  # unused, just for a draw handle pattern
    draw_monogram(img, d, size)
    img.save(path)


make_standard(192, OUT / "icon-192.png")
make_standard(512, OUT / "icon-512.png")
make_maskable(192, OUT / "icon-maskable-192.png")
make_maskable(512, OUT / "icon-maskable-512.png")
make_apple_touch(180, OUT / "apple-touch-icon.png")
make_standard(32, HERE / "favicon.png")

for p in sorted(OUT.glob("*.png")) + [HERE / "favicon.png"]:
    print(p.relative_to(HERE), Image.open(p).size)

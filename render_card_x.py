"""
Edge Decoded (X) — single hero-card renderer.

Builds the ONE image that rides on the hook tweet: the cinematic gpt-image hero,
full-bleed, darkened with a bottom gradient, framed with the Edge Decoded label
pill (top-left), the bold headline (bottom-left, one word highlighted in the
day's accent), and @decodededge (bottom-right).

Card is 1600x900 (16:9) so X never crops it in the timeline.

Usage:
    python render_card_x.py                 # renders sample_thread.json
    python render_card_x.py path/to.json
"""
import datetime as _dt
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

# ---- canvas + brand ----------------------------------------------------------
W, H = 1600, 900
M = 90
BG = (10, 10, 10)
WHITE = (255, 255, 255)
INK = (10, 10, 10)
ACCENT = (200, 255, 0)          # overridden per-day

PALETTES = [
    ("lime",   (200, 255, 0)),
    ("cyan",   (0, 229, 255)),
    ("pink",   (255, 61, 165)),
    ("orange", (255, 106, 0)),
    ("yellow", (255, 212, 0)),
    ("violet", (157, 123, 255)),
]

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "fonts")
OUT_DIR = os.path.join(HERE, "output")
_ANTON = os.path.join(FONT_DIR, "Anton-Regular.ttf")
_INTER = os.path.join(FONT_DIR, "Inter-Variable.ttf")


def pick_palette(seed=None):
    if seed is None:
        seed = _dt.date.today().toordinal()
    return PALETTES[seed % len(PALETTES)]


def anton(size):
    return ImageFont.truetype(_ANTON, size)


def inter(size, weight=600):
    f = ImageFont.truetype(_INTER, size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def tw(draw, text, font, tracking=0):
    if not text:
        return 0
    return draw.textlength(text, font=font) + tracking * (len(text) - 1)


def draw_tracked(draw, xy, text, font, fill, tracking=0):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + tracking


# ---- hero image: cover-fill the canvas + darkening gradient ------------------
def _paste_cover(img, path):
    hero = Image.open(path).convert("RGB")
    scale = max(W / hero.width, H / hero.height)
    hero = hero.resize((int(hero.width * scale), int(hero.height * scale)))
    x = (hero.width - W) // 2
    y = (hero.height - H) // 2
    img.paste(hero.crop((x, y, x + W, y + H)), (0, 0))


def _bottom_gradient(img, frac=0.62, strength=235):
    """Darken the lower portion so the headline reads cleanly."""
    grad = Image.new("L", (1, H), 0)
    start = int(H * (1 - frac))
    for y in range(start, H):
        t = (y - start) / max(1, (H - start))
        grad.putpixel((0, y), int(strength * (t ** 1.4)))
    alpha = grad.resize((W, H))
    black = Image.new("RGB", (W, H), (0, 0, 0))
    img.paste(Image.composite(black, img, alpha), (0, 0))


# ---- headline (auto-fit, one phrase highlighted) -----------------------------
def _wrap(draw, words, font, max_w):
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if tw(draw, trial, font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _draw_headline(draw, text, highlight, box, max_size=120):
    bx, by, bw, bh = box
    text = (text or "").upper().strip()
    hl = {w.strip(",.:;!?") for w in (highlight or "").upper().split()}
    words = text.split()
    size = max_size
    while size > 40:
        font = anton(size)
        lh = int(size * 1.02)
        lines = _wrap(draw, words, font, bw)
        if len(lines) * lh <= bh and all(tw(draw, ln, font) <= bw for ln in lines):
            break
        size -= 4
    font = anton(size)
    lh = int(size * 1.02)
    lines = _wrap(draw, words, font, bw)
    y = by + bh - len(lines) * lh           # bottom-aligned
    space_w = draw.textlength(" ", font=font)
    for ln in lines:
        x = bx
        for word in ln.split():
            color = ACCENT if word.strip(",.:;!?") in hl else WHITE
            draw.text((x, y), word, font=font, fill=color)
            x += draw.textlength(word, font=font) + space_w
        y += lh


def _label_pill(draw, text):
    text = (text or "DECODED").upper()
    f = inter(30, 800)
    pad_x, pad_y = 22, 14
    txt_w = tw(draw, text, f, tracking=2)
    draw.rounded_rectangle([M, M, M + txt_w + pad_x * 2, M + 30 + pad_y * 2],
                           radius=8, fill=ACCENT)
    draw_tracked(draw, (M + pad_x, M + pad_y), text, f, INK, tracking=2)


def render_card(thread, out_path=None):
    global ACCENT
    ACCENT = tuple(thread.get("accent_rgb") or pick_palette()[1])
    out_path = out_path or os.path.join(OUT_DIR, "card.png")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    img = Image.new("RGB", (W, H), BG)
    hero = thread.get("image")
    if hero and os.path.exists(os.path.join(HERE, hero)):
        _paste_cover(img, os.path.join(HERE, hero))
    _bottom_gradient(img)
    draw = ImageDraw.Draw(img)

    _label_pill(draw, thread.get("label"))

    # handle: top-right, aligned with the label pill (never collides with headline)
    handle = thread.get("handle", "@decodededge")
    fh = inter(32, 800)
    draw.text((W - M - tw(draw, handle, fh), M + 12), handle, font=fh, fill=WHITE)

    _draw_headline(draw, thread.get("headline", thread.get("chosen_title", "")),
                   thread.get("highlight"), (M, H - 320, W - 2 * M, 250))
    img.save(out_path)
    return out_path


if __name__ == "__main__":
    spec = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "sample_thread.json")
    with open(spec, encoding="utf-8") as fh:
        thread = json.load(fh)
    out = render_card(thread)
    print("wrote", out)

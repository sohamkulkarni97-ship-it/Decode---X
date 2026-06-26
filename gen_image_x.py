"""
Edge Decoded (X) — cinematic hero-image generator (OpenAI gpt-image-1).

Unlike the Instagram cartoons, the X bot posts ONE image per thread, so it needs
to be dramatic and scroll-stopping on its own. This makes a bold, high-contrast,
cinematic editorial image (no text) that render_card_x.py then frames with the
Edge Decoded headline + handle.

Env: OPENAI_API_KEY must be set.
"""
import base64
import os

from openai import OpenAI

MODEL = "gpt-image-1"

# Cinematic, premium, single-hero look. Dark + one accent so the headline overlay
# (added later in Pillow) stays legible and on-brand. This is a thick, art-directed
# style block so even a short story prompt yields a striking, gallery-grade image.
STYLE = (
    "Award-winning, ultra-premium editorial KEY ART for a science/curiosity brand — the "
    "single hero image that has to stop the scroll on its own. Treat it like a cover shot. "
    "ART DIRECTION: one bold, instantly-readable focal subject or visual metaphor that "
    "captures the idea; cinematic wide composition with strong depth, layered foreground "
    "and background, and a clear sense of scale and drama. Render with rich detail and "
    "tactile texture — think 8K, sharp focus on the subject with gentle depth-of-field "
    "falloff behind it. "
    "LIGHTING & MOOD: moody, dramatic, high-contrast chiaroscuro lighting; a deep, almost "
    "black background; bold volumetric rim-light and a glowing {accent} accent as the hero "
    "color threading through the scene, plus one or two restrained complementary pops. "
    "Cinematic color grade, subtle atmosphere (haze, dust, particles, or bokeh) for depth. "
    "STYLE: lean photoreal-meets-stylized-3D editorial illustration — striking and "
    "imaginative, never a flat clip-art icon, never a stocky generic photo. Make a bold, "
    "unexpected creative choice that makes the viewer look twice. "
    "COMPOSITION RULES: keep the main subject in the UPPER TWO-THIRDS and keep the LOWER "
    "THIRD clean, dark and uncluttered (a headline will be overlaid there). Negative space "
    "is good. "
    "STRICTLY FORBIDDEN: any text, letters, words, numbers, captions, labels, signage, "
    "logos, watermarks, UI, frames or borders anywhere in the image. "
    "THE SCENE TO ILLUSTRATE: "
)


def generate(image_prompt, out_path, accent_hex="#C8FF00", size="1536x1024", quality="high"):
    client = OpenAI()
    res = client.images.generate(
        model=MODEL,
        prompt=STYLE.format(accent=accent_hex) + image_prompt,
        size=size,
        quality=quality,
        n=1,
    )
    data = base64.b64decode(res.data[0].b64_json)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as fh:
        fh.write(data)
    return out_path


if __name__ == "__main__":
    import sys
    p = sys.argv[1] if len(sys.argv) > 1 else (
        "an ancient cracked clay jar overflowing with glowing golden honey, a single "
        "drip frozen mid-fall, deep black background, dramatic rim light")
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "hero_test.png")
    generate(p, out)
    print("wrote", out)

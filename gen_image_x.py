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

# Shared base: composition + technical rules that apply no matter the mood.
_BASE = (
    "Award-winning, ultra-premium editorial KEY ART for a science/curiosity brand — the "
    "single hero image that has to stop the scroll on its own. Treat it like a cover shot. "
    "Render with rich detail and tactile texture — think 8K, sharp focus on the subject "
    "with gentle depth-of-field falloff behind it. Make a bold, unexpected creative choice "
    "that makes the viewer look twice. "
    "COMPOSITION RULES: keep the main subject in the UPPER TWO-THIRDS and keep the LOWER "
    "THIRD clean and uncluttered (a headline will be overlaid there). Negative space is good. "
    "STRICTLY FORBIDDEN: any text, letters, words, numbers, captions, labels, signage, "
    "logos, watermarks, UI, frames or borders anywhere in the image. "
)

# Visual MOODS the content engine picks per story, so the page doesn't look like
# the same dark-moody shot every single day. Each still threads the day's accent
# color through the scene so the brand stays recognizable.
MODES = {
    # dark, dramatic, high-contrast — collapses, mysteries, unsettling science, history
    "cinematic": (
        "ART DIRECTION: one bold, instantly-readable focal subject or visual metaphor; "
        "cinematic wide composition with strong depth and a clear sense of scale and drama. "
        "LIGHTING & MOOD: moody, dramatic, high-contrast chiaroscuro lighting; a deep, "
        "almost black background; bold volumetric rim-light and a glowing {accent} accent "
        "as the hero color threading through the scene, plus one or two restrained "
        "complementary pops. Cinematic color grade, subtle atmosphere (haze, dust, "
        "particles) for depth. STYLE: lean photoreal-meets-stylized-3D, never flat clip-art. "
    ),
    # bright, punchy, energetic — amazing/feel-good stories, business wins, big numbers
    "vibrant": (
        "ART DIRECTION: one bold, joyful, larger-than-life focal subject or moment, caught "
        "mid-action with real energy and movement. LIGHTING & MOOD: bright, saturated, "
        "punchy daylight or studio lighting; a rich, deep-toned background (not pure black) "
        "with the {accent} color used boldly and confidently across the scene, plus one or "
        "two vivid complementary pops. Crisp, optimistic, high-energy color grade. STYLE: "
        "lean photoreal-meets-stylized-3D editorial illustration, vivid and alive. "
    ),
    # clean, graphic, conceptual — AI, finance mechanisms, abstract ideas
    "technical": (
        "ART DIRECTION: one bold, clean conceptual object or visual metaphor on an "
        "uncluttered studio-style backdrop — graphic, almost product-shot precision, "
        "instantly readable as an idea rather than a literal scene. LIGHTING & MOOD: "
        "crisp directional studio lighting, a deep near-black or dark-graphite background, "
        "a glowing {accent} accent light defining the object's edges precisely, minimal "
        "and confident. STYLE: precise, high-end 3D-render quality, premium tech-editorial. "
    ),
    # warm, human, emotional — psychology, human-interest, pharma/health stories
    "warm": (
        "ART DIRECTION: one bold, intimate human or emotionally resonant focal subject, "
        "caught in a genuine, telling moment. LIGHTING & MOOD: warm golden-hour or soft "
        "window light, a rich warm-toned dark background, the {accent} color appearing as "
        "a gentle glow or reflected light rather than a hard rim-light. Tender, atmospheric, "
        "cinematic color grade with soft haze. STYLE: photoreal-meets-stylized-3D, warm and "
        "human, never clinical or sterile. "
    ),
}


def generate(image_prompt, out_path, accent_hex="#C8FF00", mode="cinematic",
            size="1536x1024", quality="high"):
    client = OpenAI()
    style = MODES.get(mode, MODES["cinematic"]).format(accent=accent_hex)
    res = client.images.generate(
        model=MODEL,
        prompt=_BASE + style + "THE SCENE TO ILLUSTRATE: " + image_prompt,
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

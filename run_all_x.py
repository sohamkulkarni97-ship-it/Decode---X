"""
Edge Decoded (X) — thread build (no publishing).

fetch -> Sonnet pick+write thread -> generate the single cinematic hero ->
render the hero card. Produces output/today_thread.json and output/card.png.
The workflow runs this, commits output/, then runs publish_x.py.

Usage:
  python run_all_x.py
"""
import json
import os

import fetch
import pick_and_write_x as engine
import render_card_x as card


def _add_hero(thread, accent_hex):
    """Generate the single cinematic hero image (best-effort)."""
    prompt = thread.get("image_prompt")
    if not prompt:
        print("[note] no image_prompt — card will be text-only on black.")
        return
    if not os.environ.get("OPENAI_API_KEY"):
        print("[note] OPENAI_API_KEY not set — card will be text-only on black.")
        return
    import gen_image_x
    rel = os.path.join("assets", "hero.png")
    try:
        gen_image_x.generate(prompt, os.path.join(engine.HERE, rel), accent_hex=accent_hex)
        thread["image"] = rel
        print(f"  hero -> {rel}  ({prompt[:56]}...)")
    except Exception as e:
        print(f"  [warn] hero gen failed ({e}); card will be text-only.")


def main():
    cands = fetch.fetch_candidates()
    if not cands:
        raise SystemExit("No fresh candidates today.")
    print(f"Fetched {len(cands)} candidates.")
    thread = engine.generate_thread(cands, avoid_lanes=engine._recent_lanes())
    print(f"Chosen [{thread.get('lane')}] (score {thread.get('score')}): {thread.get('chosen_title')}")

    name, rgb = card.pick_palette()
    accent_hex = "#%02X%02X%02X" % rgb
    thread["palette"] = name
    thread["accent_rgb"] = list(rgb)
    print(f"Palette: {name} ({accent_hex})")

    _add_hero(thread, accent_hex)

    out = os.path.join(engine.HERE, "output", "today_thread.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(thread, fh, indent=2, ensure_ascii=False)

    card.render_card(thread)
    print(f"Rendered hero card -> output/card.png")
    print(f"Thread: {len(thread.get('tweets', []))} tweets -> {out}")


if __name__ == "__main__":
    main()

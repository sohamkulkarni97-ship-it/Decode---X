"""
Edge Decoded (X) — content engine (Claude Sonnet 4.6).

Takes fresh candidates from fetch.py, asks Sonnet to (1) score them, (2) pick
the single best story, and (3) write it as an X THREAD: one hook tweet (which
carries the single hero image) plus a reply chain, each tweet <= 280 chars and
LINK-FREE (links would cost 13x more per tweet under X's pay-per-use pricing).

Output is thread-JSON consumed by render_card_x.py (the hero card) and
publish_x.py (the thread poster).

Env: ANTHROPIC_API_KEY must be set.

Usage:
    python pick_and_write_x.py     # fetch -> Sonnet -> writes output/today_thread.json
"""
import json
import os
import re

import anthropic

import fetch
import trends

HERE = os.path.dirname(os.path.abspath(__file__))
POSTED_LOG = os.path.join(HERE, "posted.json")
OUT = os.path.join(HERE, "output", "today_thread.json")

MODEL = "claude-sonnet-4-6"
HANDLE = "@decodededge"
MAX_TWEET = 280

SYSTEM = f"""You are the editor of Edge Decoded ({HANDLE}), a daily X (Twitter)
account that explains the single most interesting thing happening in finance, AI,
science, space, business, psychology, pharma, history ("on this day"), and the kind
of incredible/unbelievable real-life stories people can't help but share.
Your voice: sharp, factual, scroll-stopping. Never hype, never clickbait the story
can't back up. Always attribute the real source.

You will receive a list of fresh news candidates. Do two jobs:

1) SCORE each candidate 0-100 for X engagement using this rubric:
   - Surprise ("wait, what?") - 30
   - Personal impact (health, money, daily life) - 25
   - "I have to tell someone this" shareability - 20
   - Thread potential (a story with 4-7 real beats to unpack) - 15
   - Timeliness - 10
   Avoid: dry procedural news, partisan politics, anything ambiguous or unverifiable.
   TREND BOOST (light): some candidates are marked "🔥TRENDING" and a "TRENDING NOW"
   list of hot terms may be given. Give a MODERATE boost (a few points) to on-brand
   candidates that match what's trending right now — timeliness helps reach. But never
   let a trend override lane fit, a real source, or genuine "wow" quality, and IGNORE
   off-brand trends entirely (sports, celebrity gossip, partisan politics, movie/TV
   churn). A trend is a tie-breaker, not a mandate.

2) Pick the SINGLE highest scorer and write it as an Edge Decoded X THREAD.

THREAD RULES:
- The thread is a HOOK tweet + a REPLY CHAIN. 5 to 8 tweets total.
- TWEET 1 (the hook) is the most important. It carries the single hero image and
  must stop the scroll: a surprising claim or question, plain and punchy, ending
  with the thread emoji. Example shape: "On Venus, a single day lasts longer than
  its entire year. No, that's not a typo. 🧵"
- TWEETS 2..n-1: ONE idea each. Conversational, concrete, specific. Include the real
  names, numbers, mechanism, and the catch. This is where the substance lives — carry
  100% of the story across the chain (X has no caption, the thread IS the content).
- DENSITY: make every body tweet earn its place — aim to fill roughly 200-270 of the 280
  characters with real substance (a number, a name, a mechanism, a comparison), not
  half-empty filler. Slightly information-rich beats airy.
- SCANNABLE STRUCTURE: readers skim X, so make it easy on the eye. Wherever a tweet
  presents 2+ parallel facts, stats, examples, steps, or "who's affected", format them as
  short BULLET LINES ("• ...") on separate lines instead of a dense paragraph. Aim for
  2-3 bulleted tweets across the thread where they fit naturally. Keep the genuine
  narrative beats (what happened, the mechanism, the twist) as prose so it still reads
  like a story, not a listicle. Format a bulleted tweet like:
      A short lead line:
      • point one (tight, concrete, often with a number)
      • point two
      • point three
  Use "•" + line breaks; 2-4 bullets per such tweet; keep each tweet <= the char limit.
  Do NOT bullet the hook or the final tweet, and never force a list where prose flows better.
- FINAL TWEET: a one-line takeaway, then on a new line "Follow {HANDLE}", then on a new
  line "Source: <publication>".
- HARD LIMITS:
    * Every tweet <= {MAX_TWEET} characters INCLUDING any numbering. Count carefully.
    * NEVER include a URL or link in ANY tweet (links cost 13x more to post). Cite the
      source as PLAIN TEXT only ("Source: NASA"), never as a clickable link.
    * Do NOT prefix tweets with "1/", "2/" yourself UNLESS it reads naturally; the
      poster keeps them as separate replies regardless. Prefer clean prose over "1/n".
- Facts must come from the candidate's title/summary. You MAY add widely-known
  background clearly as context, but NEVER invent specific figures, study sizes,
  quotes, or dates not in the source.

HERO IMAGE (the single most important visual — it's the ONLY image, so make it count):
- Write "image_prompt": a RICH, art-directed scene for this exact story — 3 to 5 full
  sentences (roughly 60-110 words), not a terse line. A house cinematic style is added
  automatically, so DON'T waste words on generic style adjectives; instead spend every
  word on CONCRETE, STORY-SPECIFIC visual detail. Cover, in order:
    1. The single hero SUBJECT or visual metaphor that nails this exact idea (be specific
       and a little unexpected — the image that makes someone stop and think "what is that?").
    2. The SETTING / background and a sense of scale or depth.
    3. Two or three vivid concrete DETAILS (objects, textures, action, a telling moment).
    4. The MOOD and what a single bright accent light is doing in the scene (a beam, a
       glow, a reflection) — describe it as "a bright accent glow/beam", the brand recolors it.
  Make a bold, imaginative creative choice — surreal, dramatic, or conceptual is welcome
  as long as it reads instantly. Keep the LOWER THIRD of the frame calm/dark (headline goes
  there). NEVER describe any text, letters, numbers, logos or watermarks in the image.
- Write "image_mode": pick the VISUAL MOOD that fits this exact story — vary it day to
  day so the page doesn't look like the same dark photo every time:
    cinematic = dark, dramatic, high-contrast (collapses, mysteries, unsettling science,
                history, true-crime-ish stories)
    vibrant   = bright, punchy, energetic, saturated (amazing/feel-good stories, big wins,
                impressive numbers, "wow" discoveries)
    technical = clean, graphic, conceptual, studio-precise (AI, finance mechanisms,
                abstract ideas, "how something works")
    warm      = golden-hour, human, emotional, intimate (psychology, human-interest,
                health/pharma stories about real people)
  Choose deliberately based on the story's emotional register, not at random.
- Write "headline": a SHORT, bold hook (3-7 words) that will be overlaid on the image
  card. "highlight": the single punchiest word/number in that headline.
- Write "label": a short uppercase tag (SCIENCE, SPACE, FINANCE, AI, PSYCHOLOGY,
  BUSINESS, PHARMA, HISTORY, AMAZING, THE STORY).

OUTPUT: return ONLY a JSON object (no prose, no markdown fences). Shape:
{{
  "chosen_title": "...",
  "lane": "...",
  "source": "...",
  "score": 0,
  "label": "SCIENCE",
  "headline": "Your fan can cook you",
  "highlight": "cook",
  "image_prompt": "<3-5 sentence rich scene, no text in image>",
  "image_mode": "cinematic",
  "tweets": [
    "<hook tweet, ends with 🧵, <=280 chars>",
    "<body tweet, <=280 chars>",
    "...",
    "<final tweet: takeaway\\nFollow {HANDLE}\\nSource: <publication>>"
  ]
}}
"""


def _recent_lanes(n=3):
    if os.path.exists(POSTED_LOG):
        with open(POSTED_LOG, encoding="utf-8") as fh:
            log = json.load(fh)
        return [e.get("lane") for e in log[-n:]]
    return []


def _call_model(system, user):
    client = anthropic.Anthropic()
    # Streaming + capped effort so adaptive thinking can't eat the whole budget and
    # leave no room for the JSON output (that caused stop_reason=max_tokens, empty text).
    with client.messages.stream(model=MODEL, max_tokens=22000,
                                thinking={"type": "adaptive"},
                                output_config={"effort": "medium"}, system=system,
                                messages=[{"role": "user", "content": user}]) as stream:
        resp = stream.get_final_message()
    text = "".join(b.text for b in resp.content if b.type == "text")
    if not text.strip():
        raise RuntimeError(f"Empty model text (stop_reason={resp.stop_reason}).")
    return text


def _extract_json(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object found in model output")
    return json.loads(text[start:end + 1])


def _enforce_limits(thread):
    """Safety net: strip links and hard-trim any tweet that slipped over 280 chars."""
    clean = []
    for t in thread.get("tweets", []):
        t = re.sub(r"https?://\S+", "", t).strip()      # never allow a link
        if len(t) > MAX_TWEET:
            t = t[:MAX_TWEET - 1].rstrip() + "…"    # ellipsis
        clean.append(t)
    thread["tweets"] = [t for t in clean if t]
    return thread


def generate_thread(candidates, avoid_lanes=None, hot_terms=None):
    avoid_lanes = avoid_lanes or []
    lines = []
    for i, c in enumerate(candidates):
        flag = " 🔥TRENDING" if c.get("trending") else ""
        lines.append(f"[{i}] ({c['lane']}){flag} {c['title']} — {c['source']}\n    {c['summary'][:240]}")
    trend_block = ""
    if hot_terms:
        trend_block = ("TRENDING NOW (hot terms across the internet right now — use as a "
                       "light timeliness signal, ignore off-brand ones):\n  "
                       + "  ·  ".join(hot_terms[:20]) + "\n\n")
    user = (
        f"Recent lanes already posted (rotate away from these if quality is close): "
        f"{avoid_lanes}\n\n{trend_block}CANDIDATES:\n" + "\n".join(lines)
    )
    raw = _call_model(SYSTEM, user)
    thread = _extract_json(raw)
    thread["handle"] = HANDLE
    return _enforce_limits(thread)


if __name__ == "__main__":
    cands = fetch.fetch_candidates()
    if not cands:
        raise SystemExit("No candidates fetched.")
    print(f"Ranking {len(cands)} candidates with {MODEL}...")
    hot = trends.trend_signals()
    thread = generate_thread(cands, avoid_lanes=_recent_lanes(), hot_terms=hot)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(thread, fh, indent=2, ensure_ascii=False)
    print(f"\nCHOSEN [{thread.get('lane')}] (score {thread.get('score')}): {thread.get('chosen_title')}")
    print(f"Tweets: {len(thread.get('tweets', []))}  ->  {OUT}\n")
    for i, t in enumerate(thread.get("tweets", []), 1):
        print(f"--- tweet {i} ({len(t)} chars) ---\n{t}\n")

"""
Edge Decoded (X) — thread publisher (X API v2, OAuth 1.0a user context).

Posts the rendered thread:
  1) upload the single hero card  (media/upload)
  2) post tweet 1 (the hook) WITH the image
  3) post tweets 2..n as a reply chain (each in_reply_to the previous)

Uses OAuth 1.0a user-context keys (API key/secret + access token/secret). These
do NOT expire, so there is no token-refresh workflow to maintain.

Cost guard: every tweet is checked to be link-free before posting (a URL would
cost 13x more under X pay-per-use). Tweets over 280 chars are rejected.

Env required:
  X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET
Optional:
  DRY_RUN=1   build + validate everything, but do not post

Usage:
  python publish_x.py
"""
import datetime as dt
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
THREAD = os.path.join(HERE, "output", "today_thread.json")
CARD = os.path.join(HERE, "output", "card.png")
POSTED_LOG = os.path.join(HERE, "posted.json")
MAX_TWEET = 280


def _env(name):
    v = os.environ.get(name)
    if not v:
        raise SystemExit(f"Missing required env var: {name}")
    return v


def _validate(tweets):
    for i, t in enumerate(tweets, 1):
        if re.search(r"https?://|www\.", t):
            raise SystemExit(f"Tweet {i} contains a link — refusing (would cost 13x). Text:\n{t}")
        if len(t) > MAX_TWEET:
            raise SystemExit(f"Tweet {i} is {len(t)} chars (>{MAX_TWEET}). Text:\n{t}")


def _log_posted(thread, tweet_id):
    log = []
    if os.path.exists(POSTED_LOG):
        with open(POSTED_LOG, encoding="utf-8") as fh:
            log = json.load(fh)
    log.append({
        "key": "".join(c for c in thread.get("chosen_title", "").lower() if c.isalnum())[:60],
        "lane": thread.get("lane"),
        "title": thread.get("chosen_title"),
        "tweet_id": tweet_id,
        "date": dt.date.today().isoformat(),
    })
    with open(POSTED_LOG, "w", encoding="utf-8") as fh:
        json.dump(log, fh, indent=2, ensure_ascii=False)


def publish():
    with open(THREAD, encoding="utf-8") as fh:
        thread = json.load(fh)
    tweets = thread.get("tweets", [])
    if not tweets:
        raise SystemExit("No tweets in thread JSON.")
    _validate(tweets)

    has_card = os.path.exists(CARD)
    print(f"Thread: {len(tweets)} tweets | hero card: {'yes' if has_card else 'MISSING'}")

    if os.environ.get("DRY_RUN") == "1":
        print("DRY_RUN=1 — would post this thread:\n")
        for i, t in enumerate(tweets, 1):
            tag = "  [+image]" if i == 1 and has_card else ""
            print(f"--- tweet {i} ({len(t)} chars){tag} ---\n{t}\n")
        return

    import tweepy

    api_key = _env("X_API_KEY")
    api_secret = _env("X_API_SECRET")
    access_token = _env("X_ACCESS_TOKEN")
    access_secret = _env("X_ACCESS_SECRET")

    # v2 client for posting tweets
    client = tweepy.Client(
        consumer_key=api_key, consumer_secret=api_secret,
        access_token=access_token, access_token_secret=access_secret,
    )

    media_ids = None
    if has_card:
        # media upload still goes through the v1.1 endpoint
        auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_secret)
        v1 = tweepy.API(auth)
        media = v1.media_upload(filename=CARD)
        media_ids = [media.media_id]
        print(f"  uploaded hero card -> media_id {media.media_id}")

    # hook tweet (with image)
    first = client.create_tweet(text=tweets[0], media_ids=media_ids)
    root_id = first.data["id"]
    prev_id = root_id
    print(f"  posted hook -> {prev_id}")

    # reply chain
    for i, t in enumerate(tweets[1:], 2):
        r = client.create_tweet(text=t, in_reply_to_tweet_id=prev_id)
        prev_id = r.data["id"]
        print(f"  posted tweet {i} -> {prev_id}")

    print(f"PUBLISHED thread. root tweet id={root_id}")
    _log_posted(thread, root_id)
    return root_id


if __name__ == "__main__":
    publish()

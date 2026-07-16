#!/usr/bin/env python3
"""
Regenerate the Book Reviews cards in index.html from Pulkit's public Goodreads
RSS feed. No login, API key, or credentials required — the feed is public.

Usage:
    python3 scripts/generate_books.py            # rewrite index.html in place
    python3 scripts/generate_books.py --dry-run  # print the generated HTML only

Each card links to the public Goodreads book page, with the rating and author
taken straight from the feed (so the site always matches Goodreads). Review
pages (/review/show) are not used: Goodreads gates them behind a login wall.

To feature a new book on the site: mark it read on Goodreads, then add an entry
to FEATURED below, in display order. `title` is matched against the Goodreads
title (case- and punctuation-insensitive substring). `cover` is optional — omit
it to use the Goodreads cover image from the feed.
"""
from __future__ import annotations

import html
import re
import sys
import urllib.request
from pathlib import Path

USER_ID = "64312984"
SHELF = "read"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"

# Keep the existing OpenLibrary cover art for the current selection; new books
# added without a `cover` fall back to the Goodreads cover from the feed.
# `author` disambiguates titles that are substrings of other books on the shelf
# (e.g. "Endurance" by Lansing vs. "Endurance" by Scott Kelly). Only the surname
# needs to match, so middle-initial differences are fine.
OL = "https://covers.openlibrary.org/b/{}-L.jpg"
FEATURED = [
    {"title": "Guns, Germs, and Steel", "author": "Jared Diamond", "cover": OL.format("isbn/0393317552")},
    {"title": "Flowers for Algernon", "author": "Daniel Keyes", "cover": OL.format("isbn/0156030306")},
    {"title": "Endurance", "author": "Alfred Lansing", "cover": OL.format("id/540107")},
    {"title": "A Random Walk Down Wall Street", "author": "Burton G. Malkiel", "cover": OL.format("isbn/0393330338")},
    {"title": "Liar's Poker", "author": "Michael Lewis", "cover": OL.format("isbn/039333869X")},
    {"title": "Sapiens", "author": "Yuval Noah Harari", "cover": OL.format("isbn/0062316095")},
    {"title": "An Astronaut's Guide to Life on Earth", "author": "Chris Hadfield", "cover": OL.format("isbn/0316253014")},
    {"title": "Born a Crime", "author": "Trevor Noah", "cover": OL.format("isbn/0399588175")},
    {"title": "Educated", "author": "Tara Westover", "cover": OL.format("isbn/0399590501")},
    {"title": "Why We Sleep", "author": "Matthew Walker", "cover": OL.format("id/8814155")},
    {"title": "Factfulness", "author": "Hans Rosling", "cover": OL.format("isbn/1250107814")},
    {"title": "Surely You're Joking, Mr. Feynman!", "author": "Richard P. Feynman", "cover": OL.format("isbn/0393316041")},
    {"title": "India After Gandhi", "author": "Ramachandra Guha", "cover": OL.format("isbn/0060958588")},
    {"title": "The Ascent of Money", "author": "Niall Ferguson", "cover": OL.format("isbn/0143116177")},
    {"title": "I Do What I Do", "author": "Raghuram Rajan", "cover": OL.format("id/10872542")},
]

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"
START = "<!-- books:start"
END = "<!-- books:end -->"


def _field(block: str, tag: str) -> str:
    m = re.search(rf"<{tag}>\s*(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?\s*</{tag}>", block, re.S)
    if not m:
        return ""
    return re.sub(r"\s+", " ", html.unescape(m.group(1))).strip()


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def fetch_feed() -> list[dict]:
    """Return every book on the shelf, walking the feed's pages (100/page)."""
    items: list[dict] = []
    for page in range(1, 11):
        url = f"https://www.goodreads.com/review/list_rss/{USER_ID}?shelf={SHELF}&page={page}"
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        xml = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
        blocks = re.findall(r"<item>(.*?)</item>", xml, re.S)
        if not blocks:
            break
        for b in blocks:
            items.append({
                "title": _field(b, "title"),
                "author": _field(b, "author_name"),
                "rating": _field(b, "user_rating"),
                "book_id": _field(b, "book_id"),
                "cover": _field(b, "book_large_image_url"),
            })
        if len(blocks) < 100:
            break
    return items


def build_cards(feed: list[dict]) -> str:
    cards = []
    for entry in FEATURED:
        key = _norm(entry["title"])
        candidates = [it for it in feed if key in _norm(it["title"])]
        if entry.get("author"):
            surname = _norm(entry["author"].split()[-1])
            candidates = [it for it in candidates if surname in _norm(it["author"])]
        # Prefer an exact title prefix over a longer title that merely contains it.
        match = next((it for it in candidates if _norm(it["title"]).startswith(key)), None)
        if match is None:
            match = candidates[0] if candidates else None
        if match is None:
            print(f"WARNING: no Goodreads match for {entry['title']!r} — skipped", file=sys.stderr)
            continue
        rating = int(match["rating"] or 0)
        stars = "&#9733;" * rating + "&#9734;" * (5 - rating)
        title = html.escape(entry["title"], quote=False)
        author = html.escape(entry.get("author") or match["author"], quote=False)
        cover = html.escape(entry.get("cover") or match["cover"], quote=False)
        # Link to the public book page. Goodreads gates /review/show behind a
        # login wall, so review links would break for logged-out visitors.
        href = f"https://www.goodreads.com/book/show/{match['book_id']}"
        cards.append(
            f'            <a href="{href}" target="_blank" rel="noopener noreferrer" class="book-card">\n'
            f'                <div class="book-cover">\n'
            f'                    <img src="{cover}" alt="{title}" loading="lazy">\n'
            f'                    <span class="book-overlay">{author}</span>\n'
            f'                </div>\n'
            f'                <div class="book-info">\n'
            f'                    <h3 class="book-title">{title}</h3>\n'
            f'                    <div class="book-rating">{stars}</div>\n'
            f'                </div>\n'
            f'            </a>'
        )
    return "\n".join(cards)


def main() -> int:
    feed = fetch_feed()
    print(f"Fetched {len(feed)} books from Goodreads (shelf: {SHELF}).", file=sys.stderr)
    cards = build_cards(feed)

    if "--dry-run" in sys.argv:
        print(cards)
        return 0

    src = INDEX.read_text()
    pattern = re.compile("(" + re.escape(START) + r".*?-->\n).*?(\n\s*" + re.escape(END) + ")", re.S)
    if not pattern.search(src):
        print(f"ERROR: markers {START!r} … {END!r} not found in {INDEX}", file=sys.stderr)
        return 1
    new = pattern.sub(lambda m: m.group(1) + cards + m.group(2), src, count=1)
    INDEX.write_text(new)
    count = cards.count('class="book-card"')
    print(f"Wrote {count} book cards to {INDEX}.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
Fetches the Crosshare RSS feed and merges any new puzzles into data/puzzles.yaml,
then caches each puzzle's clues in data/details/.
Run before Hugo builds: `python3 update_puzzles.py && hugo`
"""

import urllib.request
import xml.etree.ElementTree as ET
import yaml
import json
import os
import re
import sys
import time

RSS_URL     = "https://crosshare.org/api/feed/tuber"
PUZZLE_URL  = "https://crosshare.org/crosswords/{}"
MANIFEST    = os.path.join(os.path.dirname(__file__), "data", "puzzles.yaml")
DETAILS_DIR = os.path.join(os.path.dirname(__file__), "data", "details")


def fetch_rss():
    req = urllib.request.Request(RSS_URL, headers={"User-Agent": "minicryptics-builder/1.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.read()


def parse_items(xml_bytes):
    root = ET.fromstring(xml_bytes)
    channel = root.find("channel")
    items = []
    for item in channel.findall("item"):
        link  = item.findtext("link", "").strip()
        title = item.findtext("title", "").strip()
        pub_date = item.findtext("pubDate", "").strip()
        parts = link.rstrip("/").split("/")
        # URL: /crosswords/PUZZLE_ID/slug
        puzzle_id = parts[-2]
        items.append({"id": puzzle_id, "title": title, "date": pub_date})
    return items


def load_manifest():
    if not os.path.exists(MANIFEST):
        return []
    with open(MANIFEST) as f:
        return yaml.safe_load(f) or []


def save_manifest(puzzles):
    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    with open(MANIFEST, "w") as f:
        yaml.dump(puzzles, f, allow_unicode=True, default_flow_style=False)


def fetch_puzzle(puzzle_id):
    """Fetch a puzzle page from Crosshare and return its embedded puzzle JSON."""
    req = urllib.request.Request(PUZZLE_URL.format(puzzle_id),
                                 headers={"User-Agent": "minicryptics-builder/1.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        html = r.read().decode("utf-8")
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    return json.loads(m.group(1))["props"]["pageProps"]["puzzle"]


def extract_details(pz):
    """Keep only what the site renders: the clue text. Nothing else from the
    Crosshare page (answers, comments, likes, profile data) is retained."""
    clues = [{"dir": "across" if c["dir"] == 0 else "down", "num": c["num"], "clue": c["clue"]}
             for c in sorted(pz["clues"], key=lambda c: (c["dir"], c["num"]))]
    return {"size": f'{pz["size"]["cols"]}x{pz["size"]["rows"]}', "clues": clues}


def update_details(puzzles):
    """Cache clues for each puzzle in data/details/<id>.json (fetched once; puzzles don't change)."""
    os.makedirs(DETAILS_DIR, exist_ok=True)
    todo = [p for p in puzzles if not os.path.exists(os.path.join(DETAILS_DIR, f"{p['id']}.json"))]
    print(f"Fetching details for {len(todo)} puzzle(s)...")
    for i, p in enumerate(todo):
        if i:
            time.sleep(1)  # be polite to Crosshare
        try:
            details = extract_details(fetch_puzzle(p["id"]))
        except Exception as e:
            print(f"WARNING: Could not fetch details for {p['id']}: {e}", file=sys.stderr)
            continue
        with open(os.path.join(DETAILS_DIR, f"{p['id']}.json"), "w") as f:
            json.dump(details, f, ensure_ascii=False, indent=1)


def main():
    update_manifest()
    update_details(load_manifest())


def update_manifest():
    print("Fetching RSS feed...")
    try:
        xml_bytes = fetch_rss()
    except Exception as e:
        print(f"WARNING: Could not fetch RSS feed: {e}", file=sys.stderr)
        print("Continuing with existing manifest.")
        return

    rss_items = parse_items(xml_bytes)
    print(f"Found {len(rss_items)} items in feed.")

    existing     = load_manifest()
    existing_ids = {p["id"] for p in existing}

    new_items = [p for p in rss_items if p["id"] not in existing_ids]
    if new_items:
        print(f"Adding {len(new_items)} new puzzle(s): {[p['title'] for p in new_items]}")
        # Prepend new items (RSS is newest-first, manifest should be too)
        updated = new_items + existing
        save_manifest(updated)
    else:
        print("No new puzzles found.")


if __name__ == "__main__":
    main()

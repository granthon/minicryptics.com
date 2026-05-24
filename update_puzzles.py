#!/usr/bin/env python3
"""
Fetches the Crosshare RSS feed and merges any new puzzles into data/puzzles.yaml.
Run before Hugo builds: `python3 update_puzzles.py && hugo`
"""

import urllib.request
import xml.etree.ElementTree as ET
import yaml
import os
import sys

RSS_URL  = "https://crosshare.org/api/feed/tuber"
MANIFEST = os.path.join(os.path.dirname(__file__), "data", "puzzles.yaml")


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


def main():
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

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Static site for **minicryptics.com** — a landing page listing mini cryptic crosswords, each of which embeds a puzzle hosted on [Crosshare](https://crosshare.org/tuber) via an iframe. Built with Hugo. The site itself hosts no puzzle data beyond a manifest of Crosshare puzzle IDs and titles.

## Build & develop

```bash
python3 update_puzzles.py && hugo   # full production build
hugo server                          # local dev server with live reload
hugo                                 # build only, output to public/
```

- **Production** is a nightly cron job on NearlyFreeSpeech.net (configured via their web UI, not in this repo). It runs a script that does, in order (no `set -e`, so a failed step does not stop the rest): `cd /home/private/minicryptics.com`, `git pull`, `python3 update_puzzles.py`, `~/bin/hugo --destination /home/public`. The server's working copy persists between runs, which is why the git-ignored `data/` files accumulate there. Hugo must be new enough for `hugo.Data`.
- `update_puzzles.py` requires `pyyaml`. It fetches the Crosshare RSS feed (`https://crosshare.org/api/feed/tuber`) and **prepends** any puzzle IDs not already in `data/puzzles.yaml`. On network failure it warns and continues with the existing manifest, so builds are resilient.
- It then caches each puzzle's clue text in `data/details/<id>.json`, scraped once per puzzle from the `__NEXT_DATA__` JSON on the Crosshare puzzle page. Only clue text is kept — no answers, comments, likes or profile fields. Like the manifest, the cache is **git-ignored** and lives on the server: committing it would make the nightly `git pull` fail on untracked files the server already created.
- There are no tests or linters in this repo.

## Architecture

The whole site is generated from one data file, `data/puzzles.yaml` (git-ignored — maintained on the server by the nightly build). Each entry is `{ id, title, date }` where `id` is the Crosshare puzzle ID, newest first.

Two things consume that manifest:

1. **`content/puzzle/_content.gotmpl`** — a Hugo *content adapter* that calls `$.AddPage` once per manifest entry to synthesize a page (no Markdown files exist for puzzles). Page path is `(lower .id)`, so **URLs are the lowercased puzzle ID** even though the manifest stores the original mixed-case ID. The original-case ID is passed through as `.Params.puzzleid`.
2. **`layouts/index.html`** — the homepage, which ranges over `hugo.Data.puzzles` directly to render the list.

`layouts/puzzle/single.html` renders each puzzle page, and `layouts/partials/clues.html` adds the clues as crawlable text below the iframe. The content adapter also uses the first clue in each page's meta description.

**Setter's notes** are unique to this site (deliberately *not* copied from Crosshare): write `assets/notes/<lowercased puzzle id>.md` (the URL slug) and the content adapter makes it the page's content, rendered under the clues. `||spoiler||` markup becomes `.spoiler` spans, applied *after* Markdown rendering (Goldmark would strip raw HTML).

The page embeds `https://crosshare.org/embed/{puzzleid}/{crosshareUser}` in an iframe. `crosshareUser` (the Crosshare author ID) lives in `hugo.toml` under `[params]`.

`disableKinds = ["section", "taxonomy", "term"]` in `hugo.toml` keeps Hugo from generating section/tag/category pages — only the home page and the individual puzzle pages are wanted.

## SEO / head tags

Both `layouts/index.html` and `layouts/puzzle/single.html` include the shared `layouts/partials/head.html` partial, which emits the `description`/`og:` meta tags and the favicon link (`/favicon.512.png`, served from `static/`). The partial resolves the description as `or .Description .Site.Params.description`: puzzle pages get their own description (set by the content adapter), and pages without one (e.g. the homepage) fall back to the site-wide default. That default lives in `hugo.toml` under `[params].description` — **not** the top-level `description` key — so keep it there.

The partial also emits a `<link rel="canonical">`, which matters because the clue text duplicates Crosshare's. `layouts/robots.txt` (enabled by `enableRobotsTXT`) points crawlers at the sitemap. Sitemap priority comes from `[sitemap]` in `hugo.toml` for the homepage, but content-adapter pages ignore that default, so the adapter sets `sitemap` on each puzzle page itself.

## Adding puzzles manually

To backfill historical puzzles (not in the RSS feed), add entries to `data/puzzles.yaml` by hand in the same `id`/`title`/`date` format, newest first. See the comment block at the top of that file.

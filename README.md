# minicryptics.com

Static site for minicryptics.com, built with Hugo 0.126+.
Fetches puzzles from the Crosshare RSS feed at build time.

## How it works

- `layouts/index.html` fetches https://crosshare.org/api/feed/tuber at build time
  and renders a linked list of puzzles.
- `content/puzzle/_content.gotmpl` is a Hugo content adapter that generates one
  page per puzzle from the same feed — no markdown files needed.
- `layouts/puzzle/single.html` renders each puzzle page with a Crosshare embed iframe.

URLs look like: minicryptics.com/puzzle/PUZZLE_ID/

## Deploy (one-time)

1. Push this folder to a GitHub repo
2. Go to https://app.netlify.com → "Add new site" → "Import an existing project"
3. Pick your repo — Netlify reads netlify.toml automatically
4. Deploy. Then add minicryptics.com under Site settings → Domain management.

To pick up new puzzles automatically, set a scheduled build in Netlify:
Site settings → Build & deploy → Build hooks → create a hook, then add a
daily cron job via cron-job.org pointing at that URL.

## Local preview

  brew install hugo   # needs 0.126.0+
  hugo server

Then open http://localhost:1313

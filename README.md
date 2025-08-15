# Cybersecurity RSS Aggregator (Free)

A zero-cost cybersecurity RSS aggregation site.  
**Hosting**: GitHub Pages (free)  
**Updater**: GitHub Actions (free minutes for public repos)  
**Stack**: Python (`feedparser`, `Jinja2`) → static HTML

## Features
- Aggregates multiple security feeds into one page
- Client-side search
- Sources page with per-source latest items
- JSON index (`data/posts.json`) for tinkering/automation
- Runs on a schedule (every 3 hours by default) via GitHub Actions

## Quick Start
1. Create a new **public** GitHub repo and upload these files (or push with git).
2. Enable **GitHub Pages** in Settings → Pages → Deploy from branch: `gh-pages` (the workflow will create it on first run).
3. Edit `feeds.json` to your liking.
4. Manually run the workflow (**Actions → Update & Build → Run workflow**) or wait for the schedule.

## Change Feeds
Edit `feeds.json`:
```json
{
  "sources": [
    {"name": "Krebs on Security", "url": "https://krebsonsecurity.com/feed/", "category": "General"}
  ]
}
```

## Local Test
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/update.py
python -m http.server 8080
# visit http://localhost:8080
```

## Notes
- To stay within free limits, the workflow trims to 10 sources and limits items per source and overall. Tune via env vars in the workflow.
- Some sites block bots. If a source fails, try later or remove it.
- This is a starter; PRs welcome.

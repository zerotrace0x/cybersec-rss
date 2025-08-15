#!/usr/bin/env python3
"""
Fetch RSS feeds, normalize to JSON, and render a static site with Jinja2.
Intended to run via GitHub Actions on a schedule (and manually).
"""
import json, time, re, os, hashlib, datetime, html
from urllib.parse import urlparse
import feedparser
import requests
from jinja2 import Environment, FileSystemLoader, select_autoescape

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
DATA_DIR = os.path.join(ROOT, "data")
TEMPLATES_DIR = os.path.join(ROOT, "templates")
STATIC_DIR = os.path.join(ROOT, "static")
OUTPUT_DIR = ROOT  # write HTML at repo root for GitHub Pages

MAX_ITEMS_PER_SOURCE = int(os.getenv("MAX_ITEMS_PER_SOURCE", "50"))
MAX_TOTAL_ITEMS = int(os.getenv("MAX_TOTAL_ITEMS", "400"))

def strip_html(text, maxlen=300):
    if not text:
        return ""
    # crude strip
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:maxlen]

def fetch_feed(url, timeout=20):
    # Some feeds may require requests to avoid SSL oddities / redirects
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "CyberSecRSS/1.0"})
        r.raise_for_status()
        content = r.content
        parsed = feedparser.parse(content)
    except Exception:
        parsed = feedparser.parse(url)
    return parsed

def normalize_entry(entry, source):
    link = entry.get("link") or ""
    title = entry.get("title") or "(untitled)"
    summary = entry.get("summary") or entry.get("description") or ""
    published_parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if published_parsed:
        published = time.strftime("%Y-%m-%d %H:%M:%S", published_parsed)
        ts = int(time.mktime(published_parsed))
    else:
        published = ""
        ts = int(time.time())
    guid = entry.get("id") or link or title
    uid = hashlib.sha1((source["name"] + guid).encode("utf-8")).hexdigest()
    return {
        "id": uid,
        "source": source["name"],
        "source_category": source.get("category", "General"),
        "title": title.strip(),
        "link": link,
        "summary": strip_html(summary, 500),
        "published": published,
        "timestamp": ts
    }

def main():
    with open(os.path.join(ROOT, "feeds.json")) as f:
        feeds = json.load(f)["sources"]

    items = []
    per_source = {}

    for src in feeds:
        parsed = fetch_feed(src["url"])
        entries = parsed.get("entries", [])[:MAX_ITEMS_PER_SOURCE]
        normalized = [normalize_entry(e, src) for e in entries]
        items.extend(normalized)
        per_source[src["name"]] = normalized

    # sort by timestamp desc and trim
    items.sort(key=lambda x: x["timestamp"], reverse=True)
    items = items[:MAX_TOTAL_ITEMS]

    # save JSON index
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(os.path.join(DATA_DIR, "posts.json"), "w") as f:
        json.dump({"generated_at": int(time.time()), "items": items}, f, indent=2)

    # prepare Jinja
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # render index.html
    index_t = env.get_template("index.html.j2")
    with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_t.render(items=items))

    # render sources page
    sources_t = env.get_template("sources.html.j2")
    with open(os.path.join(OUTPUT_DIR, "sources.html"), "w", encoding="utf-8") as f:
        f.write(sources_t.render(feeds=feeds, per_source=per_source))

    # copy static (noop here, but keep for future)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

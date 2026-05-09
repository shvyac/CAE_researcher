#!/usr/bin/env python3
"""
fetch_cae_news.py — weekly CAE news fetcher
Reads   ~/CAE_researcher/src/data/caeTargets.json
Reads   ~/CAE_researcher/src/data/caeSystems.json
Writes  path set by DEPLOYED_JSON env var (default: ~/cae_systems.json)
Cron:   0 6 * * 1 /path/to/venv/bin/python /path/to/fetch_cae_news.py >> /path/to/cae_news.log 2>&1

Hexagon SimCompanion targets (marked "simcompanion": true in caeTargets.json) are
fetched via the separate fetch_hexagon_simcompanion.py script which requires
COVEO_ORG_ID and COVEO_TOKEN environment variables.  If those are set here, this
script will automatically invoke the simcompanion fetcher before processing other
targets.  Otherwise SimCompanion-only entries are skipped with a warning.
"""

import json
import os
import re
import logging
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup

HOME = Path.home()
REPO_DATA = HOME / "CAE_researcher/src/data"
TARGETS_JSON = REPO_DATA / "caeTargets.json"
SOURCE_JSON = REPO_DATA / "caeSystems.json"
DEPLOYED_JSON = Path(os.environ.get("DEPLOYED_JSON", str(Path.home() / "cae_systems.json")))

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}
TIMEOUT = 20
MAX_ITEMS = 5

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def format_date(raw: str) -> str:
    """Parse RFC 2822 or ISO date and return YYYY-MM-DD."""
    try:
        dt = parsedate_to_datetime(raw)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        pass
    try:
        return raw[:10]
    except Exception:
        return raw


def fetch_rss(target: dict) -> tuple[list[dict], str]:
    url = target["newsUrl"]
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
    except Exception as exc:
        log.warning(f"  x {target['name']}: {exc}")
        return [], "Unknown"

    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError as exc:
        log.warning(f"  x {target['name']}: XML parse error: {exc}")
        return [], "Unknown"

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    items: list[dict] = []

    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()

        if not title or not link:
            continue

        entry: dict = {"title": title[:200], "url": link}
        if pub:
            entry["date"] = format_date(pub)

        items.append(entry)
        if len(items) >= MAX_ITEMS:
            break

    status = "Updated" if items else "No update"
    log.info(f"  {'ok' if items else '-'} {target['name']}: {len(items)} items (RSS)")
    return items, status


def fetch_html(target: dict) -> tuple[list[dict], str]:
    url = target["newsUrl"]
    selector = target.get("selector", "article")
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
    except Exception as exc:
        log.warning(f"  x {target['name']}: {exc}")
        return [], "Unknown"

    soup = BeautifulSoup(resp.text, "html.parser")
    candidates = soup.select(selector) or soup.select("article, .news-item, li, .post")
    items: list[dict] = []

    for el in candidates:
        link = el if el.name == "a" else el.find("a", href=True)
        if not link or not link.get("href"):
            continue

        href = urljoin(base, link["href"])
        title = re.sub(r"\s+", " ", link.get_text(strip=True)).strip()

        if len(title) < 8 or not href.startswith("http"):
            continue
        if any(s in href for s in ["#", "login", "signup", "cookie", "privacy"]):
            continue

        item: dict = {"title": title[:200], "url": href}

        for tag in el.find_all(["time", "span", "p", "div"]):
            text = tag.get_text(strip=True)
            if re.search(r"\b(20\d{2})\b", text):
                item["date"] = text[:30]
                break

        items.append(item)
        if len(items) >= MAX_ITEMS:
            break

    status = "Updated" if items else "No update"
    log.info(f"  {'ok' if items else '-'} {target['name']}: {len(items)} items")
    return items, status


def fetch_news(target: dict) -> tuple[list[dict], str]:
    if target.get("rss"):
        return fetch_rss(target)
    return fetch_html(target)


def run_simcompanion_fetcher() -> None:
    """Run fetch_hexagon_simcompanion.py if Coveo credentials are present."""
    org_id = os.environ.get("COVEO_ORG_ID", "")
    token = os.environ.get("COVEO_TOKEN", "")
    if not org_id or not token:
        log.info(
            "Skipping SimCompanion fetch (COVEO_ORG_ID / COVEO_TOKEN not set). "
            "Run fetch_hexagon_simcompanion.py separately to include Hexagon portal news."
        )
        return

    script = Path(__file__).parent / "fetch_hexagon_simcompanion.py"
    if not script.exists():
        log.warning("fetch_hexagon_simcompanion.py not found at %s", script)
        return

    log.info("Running SimCompanion fetcher …")
    result = subprocess.run(
        [sys.executable, str(script)],
        env={**os.environ},
        capture_output=False,
    )
    if result.returncode != 0:
        log.warning("SimCompanion fetcher exited with code %d", result.returncode)


def main() -> None:
    targets = {t["id"]: t for t in json.loads(TARGETS_JSON.read_text())}
    systems = json.loads(SOURCE_JSON.read_text())
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    log.info(f"=== CAE news fetch started {now} ===")

    # Fetch Hexagon SimCompanion news (Coveo API) before processing other targets
    run_simcompanion_fetcher()

    # Reload systems in case simcompanion fetcher already wrote news for some entries
    if DEPLOYED_JSON.exists():
        deployed = {s["id"]: s for s in json.loads(DEPLOYED_JSON.read_text())}
    else:
        deployed = {}

    for system in systems:
        sid = system["id"]
        target = targets.get(sid)
        if target is None:
            continue

        # Skip targets that are SimCompanion-only (no newsUrl for HTML/RSS fetch)
        if target.get("simcompanion") and not target.get("newsUrl"):
            # News already written by run_simcompanion_fetcher(); copy it over if available
            if sid in deployed and deployed[sid].get("latestNews"):
                system["latestNews"] = deployed[sid]["latestNews"]
                system["lastFetched"] = deployed[sid].get("lastFetched", now)
                system["fetchStatus"] = deployed[sid].get("fetchStatus", "Updated")
            else:
                system.setdefault("fetchStatus", "Pending SimCompanion credentials")
            continue

        log.info(f"Fetching {system['name']} ...")
        news, status = fetch_news(target)

        # For SimCompanion-tagged targets with a fallback newsUrl, prefer SimCompanion
        # news if already fetched; otherwise use the HTML/RSS result
        if target.get("simcompanion") and sid in deployed and deployed[sid].get("latestNews"):
            system["latestNews"] = deployed[sid]["latestNews"]
            system["lastFetched"] = deployed[sid].get("lastFetched", now)
            system["fetchStatus"] = deployed[sid].get("fetchStatus", "Updated")
        else:
            system["latestNews"] = news
            system["lastFetched"] = now
            system["fetchStatus"] = status

    DEPLOYED_JSON.parent.mkdir(parents=True, exist_ok=True)
    DEPLOYED_JSON.write_text(json.dumps(systems, ensure_ascii=False, indent=2))
    log.info(f"=== Done -> {DEPLOYED_JSON} ===")


if __name__ == "__main__":
    main()

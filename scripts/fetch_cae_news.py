#!/usr/bin/env python3
"""
fetch_cae_news.py — weekly CAE news fetcher
Reads   ~/CAE_researcher/src/data/caeTargets.json
Reads   ~/CAE_researcher/src/data/caeSystems.json
Writes  /var/www/mysite/user/data/cae_systems.json
Cron:   0 6 * * 1 /home/shvyac/scripts/venv/bin/python /home/shvyac/scripts/fetch_cae_news.py >> /home/shvyac/scripts/cae_news.log 2>&1
"""

import json
import re
import logging
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup

HOME = Path.home()
REPO_DATA = HOME / "CAE_researcher/src/data"
TARGETS_JSON = REPO_DATA / "caeTargets.json"
SOURCE_JSON = REPO_DATA / "caeSystems.json"
DEPLOYED_JSON = Path("/var/www/mysite/user/data/cae_systems.json")

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


def fetch_news(target: dict) -> tuple[list[dict], str]:
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


def main() -> None:
    targets = {t["id"]: t for t in json.loads(TARGETS_JSON.read_text())}
    systems = json.loads(SOURCE_JSON.read_text())
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    log.info(f"=== CAE news fetch started {now} ===")

    for system in systems:
        sid = system["id"]
        if sid not in targets:
            continue
        log.info(f"Fetching {system['name']} ...")
        news, status = fetch_news(targets[sid])
        system["latestNews"] = news
        system["lastFetched"] = now
        system["fetchStatus"] = status

    DEPLOYED_JSON.parent.mkdir(parents=True, exist_ok=True)
    DEPLOYED_JSON.write_text(json.dumps(systems, ensure_ascii=False, indent=2))
    log.info(f"=== Done -> {DEPLOYED_JSON} ===")


if __name__ == "__main__":
    main()

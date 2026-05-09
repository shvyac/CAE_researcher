#!/usr/bin/env python3
"""
fetch_hexagon_simcompanion.py — Fetch "News & Product Updates" for ALL Hexagon
products from the SimCompanion portal (Coveo-powered search).

HOW TO GET YOUR COVEO CREDENTIALS
──────────────────────────────────
1. Log into https://simcompanion.hexagon.com/customers/s/article-list
2. Open DevTools → Network tab (F12 → Network)
3. In the filter box type: search/v2
4. Click any product checkbox in the left panel to trigger a search
5. Click the captured request to platform.cloud.coveo.com
6. From the request URL  → copy the value of  organizationId=…
7. From Request Headers → copy the value after "Authorization: Bearer "
8. Set environment variables:
       export COVEO_ORG_ID="your-org-id-here"
       export COVEO_TOKEN="your-bearer-token-here"

Tokens expire after ~1 hour. Re-run steps 4-8 to refresh.

OUTPUT
──────
Writes  DEPLOYED_JSON  (default: ~/cae_systems.json) — same file as
fetch_cae_news.py, merging Hexagon SimCompanion news into the systems array.

STANDALONE USAGE
────────────────
  python3 fetch_hexagon_simcompanion.py
  python3 fetch_hexagon_simcompanion.py --out /tmp/hexagon_news.json
  python3 fetch_hexagon_simcompanion.py --max-items 10
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

# ─── Paths ──────────────────────────────────────────────────────────────────
HOME = Path.home()
REPO_DATA = HOME / "CAE_researcher/src/data"
SOURCE_JSON = REPO_DATA / "caeSystems.json"
DEPLOYED_JSON = Path(os.environ.get("DEPLOYED_JSON", str(HOME / "cae_systems.json")))

# ─── Coveo config (set via env or CLI) ──────────────────────────────────────
COVEO_PLATFORM = "https://platform.cloud.coveo.com/rest/search/v2"
COVEO_ORG_ID = os.environ.get("COVEO_ORG_ID", "")
COVEO_TOKEN = os.environ.get("COVEO_TOKEN", "")

# ─── All Hexagon SimCompanion products (exact names as Coveo field values) ──
HEXAGON_PRODUCTS = [
    "Adams",
    "Actran",
    "Assembly Planner",
    "CAEfatigue",
    "Cradle CFD",
    "Digimat",
    "Dytran",
    "Easy5",
    "Flightloads",
    "Forming",
    "Marc",
    "MaterialCenter",
    "MSC Apex",
    "MSC Apex Generative Design",
    "MSC Community",
    "MSC Nastran",
    "Patran",
    "SimDesigner",
    "SimManager",
]

# Maps Coveo product name → caeSystems.json id
PRODUCT_TO_ID: dict[str, str] = {
    "Adams": "adams",
    "Actran": "actran",
    "Assembly Planner": "assembly-planner",
    "CAEfatigue": "caefatigue",
    "Cradle CFD": "cradle-cfd",
    "Digimat": "digimat",
    "Dytran": "dytran",
    "Easy5": "easy5",
    "Flightloads": "flightloads",
    "Forming": "forming",
    "Marc": "marc",
    "MaterialCenter": "materialcenter",
    "MSC Apex": "msc-apex",
    "MSC Apex Generative Design": "msc-apex-generative-design",
    "MSC Community": "msc-community",
    "MSC Nastran": "nastran",
    "Patran": "patran",
    "SimDesigner": "simdesigner",
    "SimManager": "simmanager",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Content-Type": "application/json",
    "Accept": "application/json",
}

TIMEOUT = 30

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


# ─── Coveo helpers ───────────────────────────────────────────────────────────

def _search_headers(token: str) -> dict:
    return {**HEADERS, "Authorization": f"Bearer {token}"}


def fetch_all_news(org_id: str, token: str, max_items: int) -> dict[str, list[dict]]:
    """
    Query Coveo for ALL 'News & Product Updates' articles across all products
    in a single request, then group results by product.
    Returns  {system_id: [article, …]}
    """
    url = f"{COVEO_PLATFORM}?organizationId={org_id}"
    payload = {
        "q": "",
        "aq": '@mscnormalizedarticletype=="News & Product Updates"',
        "numberOfResults": 200,
        "sortCriteria": "@mscpublisheddate descending",
        "fieldsToInclude": [
            "mscnormalizedproduct",
            "mscpublisheddate",
            "title",
            "clickuri",
            "date",
        ],
    }

    log.info("Querying Coveo for all Hexagon product news …")
    try:
        resp = requests.post(url, headers=_search_headers(token), json=payload, timeout=TIMEOUT)
        resp.raise_for_status()
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 401:
            log.error("Coveo token expired or invalid (401). Refresh COVEO_TOKEN.")
        else:
            log.error("Coveo HTTP error: %s", exc)
        return {}
    except Exception as exc:
        log.error("Coveo request failed: %s", exc)
        return {}

    data = resp.json()
    results = data.get("results", [])
    log.info("Coveo returned %d articles total", len(results))

    grouped: dict[str, list[dict]] = {}

    for result in results:
        raw_fields = result.get("raw", {})
        products = raw_fields.get("mscnormalizedproduct", [])
        if isinstance(products, str):
            products = [products]

        title = (result.get("title") or "").strip()[:200]
        uri = result.get("clickUri") or result.get("uri") or ""
        pub_date = raw_fields.get("mscpublisheddate", "") or raw_fields.get("date", "")

        article: dict = {"title": title, "url": uri}
        if pub_date:
            # Coveo dates are often epoch ms or ISO strings
            article["date"] = _parse_coveo_date(pub_date)

        for product_name in products:
            sys_id = PRODUCT_TO_ID.get(product_name)
            if sys_id is None:
                continue
            bucket = grouped.setdefault(sys_id, [])
            if len(bucket) < max_items and article not in bucket:
                bucket.append(article)

    return grouped


def fetch_product_news(product: str, org_id: str, token: str, max_items: int) -> list[dict]:
    """Fallback: fetch news for a single product."""
    url = f"{COVEO_PLATFORM}?organizationId={org_id}"
    payload = {
        "q": "",
        "aq": (
            f'@mscnormalizedarticletype=="News & Product Updates" '
            f'@mscnormalizedproduct=="{product}"'
        ),
        "numberOfResults": max_items,
        "sortCriteria": "@mscpublisheddate descending",
        "fieldsToInclude": ["mscpublisheddate", "title", "clickuri", "date"],
    }

    try:
        resp = requests.post(url, headers=_search_headers(token), json=payload, timeout=TIMEOUT)
        resp.raise_for_status()
    except Exception as exc:
        log.warning("  x %s: %s", product, exc)
        return []

    results = resp.json().get("results", [])
    items: list[dict] = []
    for r in results:
        raw = r.get("raw", {})
        title = (r.get("title") or "").strip()[:200]
        uri = r.get("clickUri") or r.get("uri") or ""
        pub_date = raw.get("mscpublisheddate", "") or raw.get("date", "")
        article: dict = {"title": title, "url": uri}
        if pub_date:
            article["date"] = _parse_coveo_date(pub_date)
        if title and uri:
            items.append(article)
    return items


def _parse_coveo_date(raw: str | int | float) -> str:
    """Return YYYY-MM-DD from Coveo date (epoch ms, epoch s, or ISO string)."""
    try:
        ts = float(raw)
        if ts > 1e10:
            ts /= 1000
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        pass
    try:
        return str(raw)[:10]
    except Exception:
        return str(raw)


# ─── Discovery: auto-detect all products from Coveo facets ──────────────────

def discover_products(org_id: str, token: str) -> list[str]:
    """
    Ask Coveo to return the facet values for mscnormalizedproduct so we
    always get the full up-to-date product list.
    """
    url = f"{COVEO_PLATFORM}?organizationId={org_id}"
    payload = {
        "q": "",
        "aq": '@mscnormalizedarticletype=="News & Product Updates"',
        "numberOfResults": 0,
        "facets": [
            {
                "field": "mscnormalizedproduct",
                "numberOfValues": 100,
                "type": "specific",
                "injectionDepth": 1000,
            }
        ],
    }
    try:
        resp = requests.post(url, headers=_search_headers(token), json=payload, timeout=TIMEOUT)
        resp.raise_for_status()
        facets = resp.json().get("facets", [])
        if facets:
            values = facets[0].get("values", [])
            return [v["value"] for v in values if v.get("numberOfResults", 0) > 0]
    except Exception as exc:
        log.warning("Could not auto-discover products: %s", exc)
    return HEXAGON_PRODUCTS


# ─── Main ────────────────────────────────────────────────────────────────────

def main(args: argparse.Namespace) -> None:
    org_id = args.org_id or COVEO_ORG_ID
    token = args.token or COVEO_TOKEN

    if not org_id or not token:
        log.error(
            "Missing credentials.\n"
            "Set COVEO_ORG_ID and COVEO_TOKEN environment variables, or use --org-id / --token.\n"
            "See the script header for instructions on obtaining these values."
        )
        sys.exit(1)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    log.info("=== Hexagon SimCompanion news fetch started %s ===", now)

    # Optionally discover live product list
    if args.discover:
        log.info("Auto-discovering products from Coveo facets …")
        live_products = discover_products(org_id, token)
        log.info("Found %d products: %s", len(live_products), live_products)
    else:
        live_products = HEXAGON_PRODUCTS

    # Fetch all news in one shot, grouped by system ID
    news_by_id = fetch_all_news(org_id, token, args.max_items)

    # For any product missing from bulk result, do individual queries
    for product in live_products:
        sys_id = PRODUCT_TO_ID.get(product)
        if sys_id and sys_id not in news_by_id:
            log.info("  individual query for %s …", product)
            items = fetch_product_news(product, org_id, token, args.max_items)
            if items:
                news_by_id[sys_id] = items

    # Log summary
    for sys_id, items in sorted(news_by_id.items()):
        log.info("  %-35s %d articles", sys_id, len(items))

    # ── Merge into deployed systems JSON ────────────────────────────────────
    out_path = Path(args.out) if args.out else DEPLOYED_JSON

    if out_path.exists():
        systems = json.loads(out_path.read_text())
    elif SOURCE_JSON.exists():
        systems = json.loads(SOURCE_JSON.read_text())
    else:
        systems = []

    # Update matching systems
    updated = set()
    for system in systems:
        sid = system["id"]
        if sid in news_by_id:
            system["latestNews"] = news_by_id[sid]
            system["lastFetched"] = now
            system["fetchStatus"] = "Updated"
            updated.add(sid)

    # Report any IDs with news but not in systems list
    missing = set(news_by_id.keys()) - updated
    if missing:
        log.warning(
            "Articles found for IDs not in systems JSON: %s  "
            "(add them to caeSystems.json to display in the UI)",
            missing,
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(systems, ensure_ascii=False, indent=2))
    log.info("=== Done → %s ===", out_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch Hexagon SimCompanion news via Coveo API")
    parser.add_argument("--org-id", default="", help="Coveo organization ID (overrides COVEO_ORG_ID)")
    parser.add_argument("--token", default="", help="Coveo Bearer token (overrides COVEO_TOKEN)")
    parser.add_argument("--max-items", type=int, default=5, help="Max articles per product (default 5)")
    parser.add_argument("--out", default="", help="Output JSON path (overrides DEPLOYED_JSON)")
    parser.add_argument(
        "--discover",
        action="store_true",
        help="Auto-discover product list from Coveo facets (requires valid credentials)",
    )
    main(parser.parse_args())

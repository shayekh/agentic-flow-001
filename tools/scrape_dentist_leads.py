"""Scrape a paginated business directory (e.g. Yellow Pages) for dentist listings
via Firecrawl and export leads to Excel.

Usage:
    python tools/scrape_dentist_leads.py --base-url "https://www.yellowpages.com/search?search_terms=dentists&geo_location_terms=Austin%2C+TX" \\
        --pages 10 --out .tmp/dentists_austin_tx.xlsx
"""

import argparse
import json
import os
import time
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

import pandas as pd
from dotenv import load_dotenv
from firecrawl import Firecrawl

DENTIST_SCHEMA = {
    "type": "object",
    "properties": {
        "businesses": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "phone": {"type": "string"},
                    "address": {"type": "string"},
                    "city": {"type": "string"},
                    "state": {"type": "string"},
                    "zip": {"type": "string"},
                    "website": {"type": "string"},
                    "categories": {"type": "array", "items": {"type": "string"}},
                    "rating": {"type": "string"},
                },
                "required": ["name"],
            },
        }
    },
    "required": ["businesses"],
}

DENTIST_PROMPT = (
    "Extract every dentist/dental practice listing card on this page. For each one "
    "return its business name, phone number, street address, city, state, zip code, "
    "website URL if shown, any category tags, and the star rating if shown "
    "(omit fields that aren't present on the card)."
)


def page_url(base_url: str, page: int) -> str:
    parts = urlsplit(base_url)
    query = dict(parse_qsl(parts.query))
    query["page"] = str(page)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def scrape_page(client: Firecrawl, url: str) -> list[dict]:
    doc = client.scrape(
        url,
        formats=[{"type": "json", "prompt": DENTIST_PROMPT, "schema": DENTIST_SCHEMA}],
    )
    data = doc.json if hasattr(doc, "json") else None
    if not data:
        return []
    return data.get("businesses", [])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True, help="First-page URL of a directory search (e.g. Yellow Pages dentist search for a city)")
    parser.add_argument("--pages", type=int, required=True, help="Total number of pages to scrape (1-indexed)")
    parser.add_argument("--out", required=True, help="Output .xlsx filename (place under --tmp-dir, e.g. .tmp/dentists.xlsx)")
    parser.add_argument("--tmp-dir", default=".tmp")
    args = parser.parse_args()

    load_dotenv()
    api_key = os.environ["FIRECRAWL_API_KEY"]
    client = Firecrawl(api_key=api_key)

    tmp_dir = Path(args.tmp_dir)
    tmp_dir.mkdir(exist_ok=True)

    all_rows = []
    for page in range(1, args.pages + 1):
        url = page_url(args.base_url, page)
        print(f"[{page}/{args.pages}] scraping {url}")

        rows = scrape_page(client, url)
        if not rows:
            print("  no listings found, retrying once...")
            time.sleep(2)
            rows = scrape_page(client, url)

        print(f"  got {len(rows)} listings")
        for row in rows:
            row["source_page"] = page
        all_rows.extend(rows)

        (tmp_dir / f"dentists_page_{page:02d}.json").write_text(json.dumps(rows, indent=2))
        time.sleep(1)

    (tmp_dir / "all_dentists_raw.json").write_text(json.dumps(all_rows, indent=2))

    df = pd.DataFrame(all_rows)
    before = len(df)
    dedup_cols = [c for c in ["name", "phone"] if c in df.columns]
    if dedup_cols:
        df = df.drop_duplicates(subset=dedup_cols)
    print(f"Deduped {before} -> {len(df)} rows")

    if "categories" in df.columns:
        df["categories"] = df["categories"].apply(lambda t: ", ".join(t) if isinstance(t, list) else t)

    rename_map = {
        "name": "Business Name",
        "phone": "Phone",
        "address": "Address",
        "city": "City",
        "state": "State",
        "zip": "Zip",
        "website": "Website",
        "categories": "Categories",
        "rating": "Rating",
        "source_page": "Source Page",
    }
    for col in rename_map:
        if col not in df.columns:
            df[col] = None
    df = df.rename(columns=rename_map)
    df = df[list(rename_map.values())]

    df.to_excel(args.out, index=False)
    print(f"Wrote {len(df)} rows to {args.out}")


if __name__ == "__main__":
    main()

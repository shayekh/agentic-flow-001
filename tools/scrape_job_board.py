"""Scrape a paginated job board via Firecrawl and export listings to Excel.

Usage:
    python tools/scrape_job_board.py --base-url "https://dailyremote.com/remote-product-jobs?search=product&location_country=Canada" \\
        --pages 21 --out dailyremote_product_jobs_canada.xlsx
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

JOB_SCHEMA = {
    "type": "object",
    "properties": {
        "jobs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "location": {"type": "string"},
                    "url": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "posted": {"type": "string"},
                    "salary": {"type": "string"},
                },
                "required": ["title", "url"],
            },
        }
    },
    "required": ["jobs"],
}

JOB_PROMPT = (
    "Extract every job listing card on this page. For each one return its "
    "job title, location (or 'Remote' if that's all that's shown), "
    "the absolute URL to the job posting, any tags/badges shown on the card "
    "(e.g. Full-time, Contract, Senior, experience level like '2-5 yrs exp'), "
    "the relative posted date/time (e.g. '2 hours ago'), and the salary range if shown "
    "(omit if not present on the card)."
)


def page_url(base_url: str, page: int) -> str:
    parts = urlsplit(base_url)
    query = dict(parse_qsl(parts.query))
    query["page"] = str(page)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def scrape_page(client: Firecrawl, url: str) -> list[dict]:
    doc = client.scrape(
        url,
        formats=[{"type": "json", "prompt": JOB_PROMPT, "schema": JOB_SCHEMA}],
    )
    data = doc.json if hasattr(doc, "json") else None
    if not data:
        return []
    return data.get("jobs", [])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--pages", type=int, required=True, help="Total number of pages to scrape (1-indexed)")
    parser.add_argument("--out", required=True, help="Output .xlsx filename (place under --tmp-dir, e.g. .tmp/jobs.xlsx)")
    parser.add_argument("--tmp-dir", default=".tmp")
    args = parser.parse_args()

    load_dotenv()
    api_key = os.environ["FIRECRAWL_API_KEY"]
    client = Firecrawl(api_key=api_key)

    tmp_dir = Path(args.tmp_dir)
    tmp_dir.mkdir(exist_ok=True)

    all_jobs = []
    for page in range(1, args.pages + 1):
        url = page_url(args.base_url, page)
        print(f"[{page}/{args.pages}] scraping {url}")

        jobs = scrape_page(client, url)
        if not jobs:
            print(f"  no jobs found, retrying once...")
            time.sleep(2)
            jobs = scrape_page(client, url)

        print(f"  got {len(jobs)} jobs")
        for job in jobs:
            job["source_page"] = page
        all_jobs.extend(jobs)

        (tmp_dir / f"page_{page:02d}.json").write_text(json.dumps(jobs, indent=2))
        time.sleep(1)

    (tmp_dir / "all_jobs_raw.json").write_text(json.dumps(all_jobs, indent=2))

    df = pd.DataFrame(all_jobs)
    before = len(df)
    df = df.drop_duplicates(subset=["url"])
    print(f"Deduped {before} -> {len(df)} rows")

    df["tags"] = df["tags"].apply(lambda t: ", ".join(t) if isinstance(t, list) else t)
    df = df.rename(columns={
        "title": "Title",
        "location": "Location",
        "url": "Job URL",
        "tags": "Tags",
        "posted": "Posted",
        "salary": "Salary",
        "source_page": "Source Page",
    })
    for col in ["Location", "Tags", "Posted", "Salary"]:
        if col not in df.columns:
            df[col] = None
    df = df[["Title", "Location", "Job URL", "Tags", "Posted", "Salary", "Source Page"]]

    df.to_excel(args.out, index=False)
    print(f"Wrote {len(df)} rows to {args.out}")


if __name__ == "__main__":
    main()

# Scrape Dentist Business Listings → Excel Lead List

## Objective
Given a city/state (or other location), pull dentist/dental-practice listings from a business directory (Yellow Pages) and compile them into a single Excel lead list with contact info for outreach.

## Required Inputs
- Location (city, state) — used to build the Yellow Pages search URL, e.g. `geo_location_terms=Austin%2C+TX`
- Number of pages to scrape (Yellow Pages shows ~30 listings/page; confirm with user before running — Firecrawl calls cost credits)
- Output filename

## Tools
- `tools/scrape_dentist_leads.py` — pass `--base-url`, `--pages`, `--out`. Uses Firecrawl's `scrape()` with a JSON-extraction format (schema-driven) to pull business name, phone, address, city/state/zip, website, categories, and rating from each page's HTML.

## Steps
1. Confirm the target location and page count with the user before running.
2. Build the base URL: `https://www.yellowpages.com/search?search_terms=dentists&geo_location_terms=<City%2C+ST>`.
3. Run `tools/scrape_dentist_leads.py` with the base URL and page range.
4. Tool writes raw per-page JSON to `.tmp/` as it goes (crash-safe) and a deduped combined `.xlsx` at the end.
5. Spot-check a handful of rows against the live site.
6. If the user wants this as a cloud deliverable rather than a local file, move/export the result to Google Sheets.

## Edge Cases / Learnings
- Dedupe by `(name, phone)` — Yellow Pages listings don't have a stable per-listing URL field extracted, so name+phone is the practical uniqueness key.
- Not every listing has a `rating` field ("X Years in Business" shows up here instead of a star rating) — treat as optional, don't fail extraction if missing.
- A handful of rows may be missing `zip` if it's folded into a non-standard address format on the card.
- One location per run — for a nationwide list, loop this tool over a list of cities/states and concatenate the resulting Excel files (dedupe again across cities in case chains like Aspen Dental have multiple branches).
- Austin, TX run (2026-07-08): 5 pages requested → 112 raw rows → 81 unique after dedup. ~1 req/sec pacing, no rate limiting hit.

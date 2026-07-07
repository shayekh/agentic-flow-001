# Scrape a Paginated Job Board → Excel

## Objective
Given a job-board search URL (with query params for search term / location / etc.) that paginates results, extract structured listings from every page and compile them into a single Excel deliverable.

## Required Inputs
- Base search URL, including query params (e.g. `search=product&location_country=Canada`)
- Total page count (or a way to detect the last page — see Edge Cases)
- Fields to extract per listing (title, company, location, URL, tags, etc.)
- Output filename

## Tools
- `tools/scrape_job_board.py` — pass `--base-url`, `--pages`, `--out`. Uses Firecrawl's `scrape()` with a JSON-extraction format (schema-driven) to pull structured listings from each page's HTML in one call per page (no manual CSS selectors needed).

## Steps
1. Confirm the field list and page range with the user before running (Firecrawl calls cost credits).
2. Run `tools/scrape_job_board.py` with the base URL and page range.
3. Tool writes raw per-page JSON to `.tmp/` as it goes (so a crash mid-run doesn't lose completed pages) and a deduped combined `.xlsx` at the end.
4. Spot-check a handful of rows against the live site.
5. Confirm total row count matches the site's stated result count (minus any expected dupes/broken cards).

## Edge Cases / Learnings
- Firecrawl's JSON-extraction format works directly off page HTML — no need to know the site's CSS structure in advance, just describe the fields wanted in the prompt/schema.
- Dedupe by job URL — some boards repeat a listing across adjacent pages if new jobs shift pagination during a slow scrape.
- **Company name is often not on list-view cards.** On DailyRemote, only the individual job detail page has the company name, buried in an image `alt` attribute, not in visible text — not worth 1 extra Firecrawl call per listing unless the user explicitly wants it (confirmed with user: skipped for the Canada/product run).
- **Sites pad late pages with a recycled "featured/recommended" block.** On DailyRemote, once real matching results ran out (~page 9), every later page repeated the same ~12 job URLs. The site's stated total result count (292) was therefore higher than the true unique count (266) — trust the deduped count, not the site's header number.
- Always spot check one page's raw `markdown` format (not just the JSON extraction) before scaling to all pages — it's the fastest way to see what's actually on the card vs. assumed.
- DailyRemote run (2026-07-08): 21 pages, ~1 req/sec pacing, no rate limiting hit, ~2 min total runtime for 21 scrape calls.

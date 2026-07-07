# Agentic Workflows Demo

A demo of the **WAT framework** (Workflows, Agents, Tools) — an architecture for building reliable AI agents by separating probabilistic reasoning from deterministic execution.

## Why WAT

When an AI agent tries to handle every step of a task directly, accuracy compounds downward fast — at 90% accuracy per step, five sequential steps only succeed 59% of the time. WAT fixes this by giving the agent a narrow job (orchestration and decision-making) while pushing actual execution into deterministic, testable code.

## Architecture

**Layer 1 — Workflows** (`workflows/`)
Markdown SOPs written in plain language. Each one defines the objective, required inputs, which tools to call, expected outputs, and known edge cases.

**Layer 2 — Agent**
Claude reads the relevant workflow, gathers the required inputs, calls tools in the right order, handles failures, and asks clarifying questions when needed. It connects intent to execution without trying to do the execution itself.

**Layer 3 — Tools** (`tools/`)
Python scripts that do the actual work — API calls, scraping, data transforms, file exports. Consistent, testable, and fast.

## Self-Improvement Loop

Every failure is a chance to make the system more robust:

1. Identify what broke
2. Fix the tool
3. Verify the fix works
4. Update the workflow with the new approach
5. Move on with a more reliable system

## What's Included

| Workflow | Tool | Description |
|---|---|---|
| [scrape_dentist_leads.md](workflows/scrape_dentist_leads.md) | [scrape_dentist_leads.py](tools/scrape_dentist_leads.py) | Scrapes dentist/dental-practice listings from Yellow Pages by location and compiles a deduped Excel lead list (name, phone, address, website, rating). |
| [scrape_job_board.md](workflows/scrape_job_board.md) | [scrape_job_board.py](tools/scrape_job_board.py) | Scrapes a paginated job board search into a deduped Excel export using schema-driven extraction — no CSS selectors required. |

Both tools use [Firecrawl](https://firecrawl.dev)'s JSON-extraction mode to pull structured data straight from page HTML, write raw per-page JSON to `.tmp/` as they go (crash-safe), and produce a deduped `.xlsx` at the end.

## Project Structure

```
.tmp/           # Temporary/intermediate files (scraped data, exports). Disposable, regenerated as needed.
tools/          # Python scripts for deterministic execution
workflows/      # Markdown SOPs defining what to do and how
.env            # API keys and environment variables (gitignored, never committed)
```

Local files in `.tmp/` are just processing scratch space. Final deliverables are meant to live in cloud services (Google Sheets, Slides, etc.) where they're directly accessible.

## Setup

1. Install dependencies:
   ```bash
   pip install firecrawl python-dotenv pandas openpyxl
   ```
2. Create a `.env` file in the project root with your Firecrawl API key:
   ```
   FIRECRAWL_API_KEY=your_key_here
   ```

## Usage

Run a tool directly:

```bash
python tools/scrape_dentist_leads.py \
  --base-url "https://www.yellowpages.com/search?search_terms=dentists&geo_location_terms=Austin%2C+TX" \
  --pages 10 --out .tmp/dentists_austin_tx.xlsx

python tools/scrape_job_board.py \
  --base-url "https://dailyremote.com/remote-product-jobs?search=product&location_country=Canada" \
  --pages 21 --out .tmp/dailyremote_product_jobs_canada.xlsx
```

Or, working with an AI agent (e.g. Claude Code): point it at the relevant workflow in `workflows/` and let it gather inputs, run the tool, and validate the output per the SOP.

## Adding a New Workflow

1. Check `tools/` first — don't build a new script if an existing one covers the task.
2. Write the workflow as a markdown SOP in `workflows/`: objective, required inputs, tools used, steps, edge cases.
3. Build or reuse the corresponding tool in `tools/`.
4. As you hit real-world issues (rate limits, malformed data, pagination quirks), fix the tool and document the learning back in the workflow file.

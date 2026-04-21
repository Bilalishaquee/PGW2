# Paragon Estimating Lead Agent

An autonomous daily lead-generation and market-research agent for Paragon Estimating.

## What It Does

- Runs once daily at **10:00 AM EST** (America/New_York).
- Maintains a persistent lead database (SQLite by default).
- Discovers leads from search engines and public web pages.
- Extracts publicly available company/contact signals.
- Scores, classifies, and deduplicates leads.
- Saves only qualified leads (`fit_score >= 60`).
- Produces a CSV containing only new leads from the current run.
- Emails a daily summary report with CSV attached.

## Quick Start

1. Create and activate a virtual environment.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill required values.
4. Run once:
   - `python main.py run-once`
5. Start scheduler (daily at 10:00 AM EST):
   - `python main.py run-scheduler`

## Commands

- `python main.py run-once` - execute one full lead generation run.
- `python main.py run-scheduler` - run daemon scheduler.
- `python main.py init-db` - initialize DB schema and seed knowledge base.

## Notes

- Uses only publicly available data.
- Does not guess email addresses.
- Deduplicates by normalized domain, email, and phone.

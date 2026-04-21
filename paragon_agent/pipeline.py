from __future__ import annotations

import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime

from .config import settings
from .db import upsert_source_performance
from .dedupe import insert_lead, lead_exists
from .extractor import build_lead_from_hit
from .knowledge import load_kb
from .models import Lead
from .reporting import export_csv, send_email_report
from .scoring import score_lead
from .sources.search import discover_hits


def run_pipeline(conn: sqlite3.Connection) -> dict:
    kb = load_kb(conn)
    hits = discover_hits(settings.serpapi_key, settings.bing_api_key, settings.max_results_per_query)

    processed = 0
    saved = 0
    new_leads: list[Lead] = []
    source_scores: dict[str, list[int]] = defaultdict(list)
    source_qualified: Counter = Counter()
    source_high_fit: Counter = Counter()

    for hit in hits[: settings.max_leads_per_run]:
        processed += 1
        lead = build_lead_from_hit(hit.title, hit.snippet, hit.url, source_url=hit.url)
        lead.estimated_fit_score, lead.confidence, rationale = score_lead(lead, kb)
        lead.reason_for_match = f"{lead.reason_for_match[:160]} | {rationale}"

        if settings.require_contact_for_save and not (lead.email or lead.phone):
            continue
        if settings.require_email_for_b2b and lead.lead_type == "B2B" and not lead.email:
            continue
        if lead.estimated_fit_score < settings.min_fit_score:
            continue
        if lead_exists(conn, lead):
            continue

        insert_lead(conn, lead)
        saved += 1
        new_leads.append(lead)
        source_scores[hit.source_name].append(lead.estimated_fit_score)
        source_qualified[hit.source_name] += 1
        if lead.estimated_fit_score >= settings.high_fit_score:
            source_high_fit[hit.source_name] += 1

    for source_name, fit_scores in source_scores.items():
        upsert_source_performance(
            conn,
            source_name=source_name,
            fit_scores=fit_scores,
            qualified_count=source_qualified[source_name],
            high_fit_count=source_high_fit[source_name],
        )

    csv_path = export_csv(new_leads)
    send_email_report(
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_username=settings.smtp_username,
        smtp_password=settings.smtp_password,
        from_email=settings.report_from_email,
        to_email=settings.report_to_email,
        leads=new_leads,
        csv_path=csv_path,
    )

    b2b = sum(1 for x in new_leads if x.lead_type == "B2B")
    b2c = sum(1 for x in new_leads if x.lead_type == "B2C")
    top_trades = Counter(x.trade_or_niche for x in new_leads).most_common(5)
    top_sources = Counter(h.source_name for h in hits).most_common(5)

    conn.execute(
        """
        INSERT INTO run_logs
        (run_timestamp, sources_scanned, leads_processed, leads_saved, b2b_count, b2c_count, top_trades_json, top_sources_json, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.utcnow().isoformat(),
            len(set(h.source_name for h in hits)),
            processed,
            saved,
            b2b,
            b2c,
            json.dumps(top_trades),
            json.dumps(top_sources),
            "No new qualified leads found today." if saved == 0 else "Run completed successfully.",
        ),
    )
    conn.commit()

    return {
        "sources_scanned": len(set(h.source_name for h in hits)),
        "leads_processed": processed,
        "leads_saved": saved,
        "csv_path": csv_path,
    }


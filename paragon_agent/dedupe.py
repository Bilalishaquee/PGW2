from __future__ import annotations

import sqlite3

from .models import Lead
from .utils import extract_domain, normalize_email, normalize_phone


def lead_exists(conn: sqlite3.Connection, lead: Lead) -> bool:
    domain = extract_domain(lead.website or lead.source_url)
    email = normalize_email(lead.email)
    phone = normalize_phone(lead.phone)

    if domain:
        row = conn.execute("SELECT 1 FROM leads WHERE domain_normalized = ? LIMIT 1", (domain,)).fetchone()
        if row:
            return True
    if email:
        row = conn.execute("SELECT 1 FROM leads WHERE email = ? LIMIT 1", (email,)).fetchone()
        if row:
            return True
    if phone:
        row = conn.execute("SELECT 1 FROM leads WHERE phone = ? LIMIT 1", (phone,)).fetchone()
        if row:
            return True
    return False


def insert_lead(conn: sqlite3.Connection, lead: Lead) -> None:
    domain = extract_domain(lead.website or lead.source_url)
    email = normalize_email(lead.email)
    phone = normalize_phone(lead.phone)
    now = __import__("datetime").datetime.utcnow().isoformat()
    conn.execute(
        """
        INSERT INTO leads (
            lead_type, company_name, contact_name, job_title, email, phone, website, linkedin_url,
            source_url, location, trade_or_niche, estimated_fit_score, intent_signal, reason_for_match,
            confidence, date_found, domain_normalized, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            lead.lead_type,
            lead.company_name,
            lead.contact_name,
            lead.job_title,
            email,
            phone,
            lead.website,
            lead.linkedin_url,
            lead.source_url,
            lead.location,
            lead.trade_or_niche,
            lead.estimated_fit_score,
            lead.intent_signal,
            lead.reason_for_match,
            lead.confidence,
            lead.date_found,
            domain,
            now,
            now,
        ),
    )
    conn.commit()


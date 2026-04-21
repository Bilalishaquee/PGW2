from __future__ import annotations

import os
import sqlite3
from datetime import datetime

from .knowledge import KnowledgeBase, save_kb


def get_conn(db_path: str) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_type TEXT NOT NULL,
            company_name TEXT NOT NULL,
            contact_name TEXT,
            job_title TEXT,
            email TEXT,
            phone TEXT,
            website TEXT,
            linkedin_url TEXT,
            source_url TEXT NOT NULL,
            location TEXT,
            trade_or_niche TEXT,
            estimated_fit_score INTEGER NOT NULL,
            intent_signal TEXT,
            reason_for_match TEXT,
            confidence TEXT,
            date_found TEXT,
            domain_normalized TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE UNIQUE INDEX IF NOT EXISTS uq_leads_domain
        ON leads(domain_normalized) WHERE domain_normalized IS NOT NULL AND domain_normalized != '';

        CREATE UNIQUE INDEX IF NOT EXISTS uq_leads_email
        ON leads(email) WHERE email IS NOT NULL AND email != '';

        CREATE UNIQUE INDEX IF NOT EXISTS uq_leads_phone
        ON leads(phone) WHERE phone IS NOT NULL AND phone != '';

        CREATE TABLE IF NOT EXISTS run_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_timestamp TEXT NOT NULL,
            sources_scanned INTEGER NOT NULL,
            leads_processed INTEGER NOT NULL,
            leads_saved INTEGER NOT NULL,
            b2b_count INTEGER NOT NULL,
            b2c_count INTEGER NOT NULL,
            top_trades_json TEXT NOT NULL,
            top_sources_json TEXT NOT NULL,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS source_performance (
            source_name TEXT PRIMARY KEY,
            last_used_at TEXT,
            qualified_leads_count INTEGER NOT NULL DEFAULT 0,
            high_fit_count INTEGER NOT NULL DEFAULT 0,
            avg_fit_score REAL NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS knowledge_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            services_json TEXT NOT NULL,
            trades_json TEXT NOT NULL,
            buyer_types_json TEXT NOT NULL,
            pain_points_json TEXT NOT NULL,
            target_industries_json TEXT NOT NULL,
            exclusions_json TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )
    conn.commit()
    seed_kb_if_missing(conn)


def seed_kb_if_missing(conn: sqlite3.Connection) -> None:
    row = conn.execute("SELECT COUNT(*) AS c FROM knowledge_base").fetchone()
    if row["c"] == 0:
        save_kb(conn, KnowledgeBase.default())


def upsert_source_performance(
    conn: sqlite3.Connection, source_name: str, fit_scores: list[int], qualified_count: int, high_fit_count: int
) -> None:
    now = datetime.utcnow().isoformat()
    row = conn.execute(
        "SELECT qualified_leads_count, high_fit_count, avg_fit_score FROM source_performance WHERE source_name = ?",
        (source_name,),
    ).fetchone()
    run_avg = (sum(fit_scores) / len(fit_scores)) if fit_scores else 0
    if row is None:
        conn.execute(
            """
            INSERT INTO source_performance(source_name, last_used_at, qualified_leads_count, high_fit_count, avg_fit_score)
            VALUES(?, ?, ?, ?, ?)
            """,
            (source_name, now, qualified_count, high_fit_count, run_avg),
        )
    else:
        total_q = row["qualified_leads_count"] + qualified_count
        total_h = row["high_fit_count"] + high_fit_count
        existing_avg = float(row["avg_fit_score"])
        updated_avg = (existing_avg + run_avg) / 2 if run_avg else existing_avg
        conn.execute(
            """
            UPDATE source_performance
            SET last_used_at = ?, qualified_leads_count = ?, high_fit_count = ?, avg_fit_score = ?
            WHERE source_name = ?
            """,
            (now, total_q, total_h, updated_avg, source_name),
        )
    conn.commit()


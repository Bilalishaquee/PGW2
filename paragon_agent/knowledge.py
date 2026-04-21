from __future__ import annotations

from dataclasses import dataclass, asdict
import json
import sqlite3
from typing import Any


@dataclass
class KnowledgeBase:
    services: list[str]
    trades: list[str]
    buyer_types: list[str]
    pain_points: list[str]
    target_industries: list[str]
    exclusions: list[str]

    @classmethod
    def default(cls) -> "KnowledgeBase":
        return cls(
            services=[
                "construction estimating",
                "quantity takeoff",
                "bid preparation",
                "scheduling",
                "trade-specific estimating",
            ],
            trades=[
                "general contracting",
                "roofing",
                "concrete",
                "framing",
                "mep",
                "electrical",
                "plumbing",
                "hvac",
                "drywall",
                "painting",
                "earthwork",
            ],
            buyer_types=[
                "general contractor",
                "subcontractor",
                "developer",
                "architect",
                "designer",
                "home builder",
                "remodeler",
            ],
            pain_points=[
                "tight bid deadlines",
                "insufficient in-house estimators",
                "high bid volume",
                "need faster takeoffs",
            ],
            target_industries=[
                "construction",
                "real estate development",
                "architecture",
                "engineering",
            ],
            exclusions=["manufacturing", "retail", "restaurants", "beauty", "medical clinics"],
        )


def load_kb(conn: sqlite3.Connection) -> KnowledgeBase:
    row = conn.execute(
        "SELECT services_json, trades_json, buyer_types_json, pain_points_json, target_industries_json, exclusions_json "
        "FROM knowledge_base ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if not row:
        return KnowledgeBase.default()
    return KnowledgeBase(
        services=json.loads(row[0]),
        trades=json.loads(row[1]),
        buyer_types=json.loads(row[2]),
        pain_points=json.loads(row[3]),
        target_industries=json.loads(row[4]),
        exclusions=json.loads(row[5]),
    )


def save_kb(conn: sqlite3.Connection, kb: KnowledgeBase) -> None:
    payload: dict[str, Any] = asdict(kb)
    conn.execute(
        """
        INSERT INTO knowledge_base
        (services_json, trades_json, buyer_types_json, pain_points_json, target_industries_json, exclusions_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            json.dumps(payload["services"]),
            json.dumps(payload["trades"]),
            json.dumps(payload["buyer_types"]),
            json.dumps(payload["pain_points"]),
            json.dumps(payload["target_industries"]),
            json.dumps(payload["exclusions"]),
        ),
    )
    conn.commit()


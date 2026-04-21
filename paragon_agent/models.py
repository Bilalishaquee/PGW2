from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class Lead:
    lead_type: str
    company_name: str
    contact_name: str
    job_title: str
    email: str
    phone: str
    website: str
    linkedin_url: str
    source_url: str
    location: str
    trade_or_niche: str
    estimated_fit_score: int
    intent_signal: str
    reason_for_match: str
    confidence: str
    date_found: str

    @classmethod
    def empty(cls) -> "Lead":
        return cls(
            lead_type="B2B",
            company_name="",
            contact_name="",
            job_title="",
            email="",
            phone="",
            website="",
            linkedin_url="",
            source_url="",
            location="",
            trade_or_niche="general construction",
            estimated_fit_score=0,
            intent_signal="",
            reason_for_match="",
            confidence="low",
            date_found=str(date.today()),
        )


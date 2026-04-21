from __future__ import annotations

from .knowledge import KnowledgeBase
from .models import Lead


def classify_buyer_type(text: str) -> str:
    lowered = text.lower()
    if "homeowner" in lowered or "residential client" in lowered:
        return "homeowner"
    if "architect" in lowered or "design" in lowered:
        return "architect/designer"
    if "developer" in lowered:
        return "developer"
    if "subcontractor" in lowered or "specialty contractor" in lowered:
        return "subcontractor"
    if "home builder" in lowered or "remodel" in lowered:
        return "home builder/remodeler"
    return "general contractor"


def score_lead(lead: Lead, kb: KnowledgeBase) -> tuple[int, str, str]:
    text = " ".join(
        [
            lead.company_name,
            lead.reason_for_match,
            lead.intent_signal,
            lead.trade_or_niche,
            lead.job_title,
        ]
    ).lower()

    score = 0

    # Buyer type fit (0-25)
    buyer_type = classify_buyer_type(text)
    if buyer_type in {
        "general contractor",
        "subcontractor",
        "developer",
        "architect/designer",
        "home builder/remodeler",
        "homeowner",
    }:
        score += 22
    else:
        score += 8

    # Trade relevance (0-20)
    if lead.trade_or_niche.lower() in [t.lower() for t in kb.trades]:
        score += 18
    else:
        score += 8

    # Intent signal (0-20)
    if "bid deadline" in lead.intent_signal.lower() or "itb" in lead.intent_signal.lower():
        score += 20
    elif "hiring activity" in lead.intent_signal.lower():
        score += 15
    elif "estimating need" in lead.intent_signal.lower() or "takeoff" in lead.intent_signal.lower():
        score += 20
    elif "project announcement" in lead.intent_signal.lower():
        score += 14
    else:
        score += 8

    # Contact quality (0-15)
    contact_score = 0
    if lead.email:
        contact_score += 10
    if lead.phone:
        contact_score += 5
    if not (lead.email or lead.phone):
        contact_score -= 8
    score += contact_score

    # Source reliability (0-10)
    if "linkedin.com" in lead.source_url or "bid" in lead.source_url.lower():
        score += 9
    else:
        score += 6

    # Geography/serviceability (0-10)
    score += 6 if lead.location else 3

    # Exclusion penalty
    if any(ex in text for ex in [e.lower() for e in kb.exclusions]):
        score -= 30

    score = max(0, min(score, 100))

    if score >= 80:
        confidence = "high"
    elif score >= 60:
        confidence = "medium"
    else:
        confidence = "low"

    reason = (
        f"Lead type={lead.lead_type}, buyer type={buyer_type}, trade={lead.trade_or_niche}, "
        f"intent={lead.intent_signal}, contacts={'yes' if (lead.email or lead.phone) else 'no'}."
    )
    return score, confidence, reason


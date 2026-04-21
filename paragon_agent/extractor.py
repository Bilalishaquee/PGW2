from __future__ import annotations

from datetime import date
from urllib.parse import urljoin, urlparse

import requests

from .models import Lead
from .utils import extract_domain, first_email, first_phone


def _fetch_page_text(url: str) -> str:
    try:
        resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code != 200:
            return ""
        text = resp.text
        return text[:40000]
    except Exception:
        return ""


def build_lead_from_hit(title: str, snippet: str, url: str, source_url: str | None = None) -> Lead:
    lead = Lead.empty()
    lead.source_url = source_url or url
    lead.website = f"{urlparse(url).scheme}://{urlparse(url).netloc}" if "://" in url else url
    lead.company_name = title.strip().split("|")[0].split("-")[0].strip()[:120]
    lead.reason_for_match = snippet[:300]
    lead.intent_signal = infer_intent_signal(f"{title} {snippet}")
    lead.date_found = str(date.today())
    lead.lead_type = infer_lead_type(f"{title}\n{snippet}")

    page = _fetch_page_text(url)
    domain_base = f"{urlparse(url).scheme}://{urlparse(url).netloc}" if "://" in url else ""
    contact_blob = _fetch_contact_blobs(domain_base, page)
    blob = f"{title}\n{snippet}\n{page}\n{contact_blob}"
    lead.email = first_email(blob)
    lead.phone = first_phone(blob)
    lead.linkedin_url = _extract_linkedin(blob)
    lead.location = infer_location(blob)
    lead.trade_or_niche = infer_trade(blob)
    lead.contact_name, lead.job_title = infer_contact_person(blob)
    return lead


def _extract_linkedin(text: str) -> str:
    needle = "linkedin.com/"
    idx = text.find(needle)
    if idx == -1:
        return ""
    start = max(0, text.rfind("http", 0, idx))
    end = text.find('"', idx)
    if end == -1:
        end = idx + 120
    return text[start:end].strip()


def infer_trade(text: str) -> str:
    lowered = text.lower()
    map_trade = {
        "roof": "roofing",
        "concrete": "concrete",
        "electrical": "electrical",
        "plumb": "plumbing",
        "hvac": "hvac",
        "mechanical": "mep",
        "framing": "framing",
        "drywall": "drywall",
        "painting": "painting",
        "excavat": "earthwork",
    }
    for token, trade in map_trade.items():
        if token in lowered:
            return trade
    return "general construction"


def infer_location(text: str) -> str:
    lowered = text.lower()
    states = [
        "texas",
        "california",
        "florida",
        "new york",
        "georgia",
        "illinois",
        "washington",
        "arizona",
        "nevada",
    ]
    for s in states:
        if s in lowered:
            return s.title()
    return ""


def infer_intent_signal(text: str) -> str:
    lowered = text.lower()
    if "bid deadline" in lowered or "invitation to bid" in lowered:
        return "Bid deadline / ITB signal"
    if "hiring estimator" in lowered or "estimator job" in lowered:
        return "Hiring activity (estimator)"
    if "takeoff" in lowered or "estimating service" in lowered:
        return "Takeoff / estimating need mentioned"
    if "new project" in lowered or "project announced" in lowered:
        return "Project announcement signal"
    if "homeowner" in lowered or "renovation" in lowered or "home addition" in lowered:
        return "Residential project/quote intent signal"
    return "General construction activity"


def infer_lead_type(text: str) -> str:
    lowered = text.lower()
    b2c_tokens = [
        "homeowner",
        "my home",
        "kitchen remodel",
        "bathroom remodel",
        "home addition",
        "house renovation",
        "residential client",
    ]
    if any(token in lowered for token in b2c_tokens):
        return "B2C"
    return "B2B"


def infer_contact_person(text: str) -> tuple[str, str]:
    lowered = text.lower()
    if "owner" in lowered:
        return "", "Owner"
    if "project manager" in lowered:
        return "", "Project Manager"
    if "estimator" in lowered:
        return "", "Estimator"
    return "", ""


def _fetch_contact_blobs(base_url: str, root_page: str) -> str:
    if not base_url:
        return ""
    candidates = ["/contact", "/contact-us", "/about", "/team", "/services", "/request-quote"]
    blobs: list[str] = []
    fetched = 0
    for path in candidates:
        if fetched >= 3:
            break
        target = urljoin(base_url, path)
        text = _fetch_page_text(target)
        if text:
            blobs.append(text[:15000])
            fetched += 1
            # Stop early once we have usable contact signals.
            if first_email(text) or first_phone(text):
                break
    if "mailto:" in root_page:
        blobs.append(root_page)
    return "\n".join(blobs)


def domain_for_lead(lead: Lead) -> str:
    return extract_domain(lead.website or lead.source_url)


from __future__ import annotations

import re
from urllib.parse import urlparse


EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_REGEX = re.compile(r"(?:\+?\d[\d\-\s().]{7,}\d)")


def extract_domain(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url if "://" in url else f"https://{url}")
    domain = parsed.netloc.lower().strip()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def normalize_email(email: str) -> str:
    return email.strip().lower() if email else ""


def normalize_phone(phone: str) -> str:
    if not phone:
        return ""
    digits = re.sub(r"\D", "", phone)
    return digits


def first_email(text: str) -> str:
    match = EMAIL_REGEX.search(text or "")
    return match.group(0) if match else ""


def first_phone(text: str) -> str:
    match = PHONE_REGEX.search(text or "")
    return match.group(0).strip() if match else ""


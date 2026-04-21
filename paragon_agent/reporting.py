from __future__ import annotations

import csv
import json
import os
import smtplib
from collections import Counter
from datetime import datetime
from email.message import EmailMessage

from .models import Lead


def export_csv(leads: list[Lead], out_dir: str = "./outputs") -> str:
    os.makedirs(out_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y_%m_%d")
    path = os.path.join(out_dir, f"new_leads_{stamp}.csv")
    fields = [
        "lead_type",
        "company_name",
        "contact_name",
        "job_title",
        "email",
        "phone",
        "website",
        "linkedin_url",
        "source_url",
        "location",
        "trade_or_niche",
        "estimated_fit_score",
        "intent_signal",
        "reason_for_match",
        "confidence",
        "date_found",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for lead in leads:
            writer.writerow({k: getattr(lead, k) for k in fields})
    return path


def build_summary(leads: list[Lead]) -> dict:
    b2b_count = sum(1 for l in leads if l.lead_type == "B2B")
    b2c_count = sum(1 for l in leads if l.lead_type == "B2C")
    trades = Counter(l.trade_or_niche for l in leads).most_common(5)
    sources = Counter(_source_host(l.source_url) for l in leads).most_common(5)
    high_fit = sorted((l for l in leads if l.estimated_fit_score >= 80), key=lambda x: x.estimated_fit_score, reverse=True)[:5]
    return {
        "total_new_leads": len(leads),
        "b2b_count": b2b_count,
        "b2c_count": b2c_count,
        "top_trades": trades,
        "top_sources": sources,
        "top_high_fit": high_fit,
    }


def _source_host(url: str) -> str:
    if "://" not in url:
        return url
    return url.split("/")[2].lower()


def send_email_report(
    smtp_host: str,
    smtp_port: int,
    smtp_username: str,
    smtp_password: str,
    from_email: str,
    to_email: str,
    leads: list[Lead],
    csv_path: str | None = None,
) -> None:
    if not (smtp_host and from_email and to_email):
        return

    summary = build_summary(leads)
    subject = f"Paragon Estimating Daily Lead Report - {datetime.now().strftime('%Y-%m-%d')}"

    if not leads:
        body = "No new qualified leads found today."
    else:
        top_leads_text = "\n".join(
            f"- {l.company_name} ({l.trade_or_niche}) score={l.estimated_fit_score} signal={l.intent_signal}"
            for l in summary["top_high_fit"]
        )
        body = (
            f"Total new leads found: {summary['total_new_leads']}\n"
            f"B2B vs B2C: {summary['b2b_count']} / {summary['b2c_count']}\n"
            f"Top trades/niches: {json.dumps(summary['top_trades'])}\n"
            f"Source breakdown: {json.dumps(summary['top_sources'])}\n"
            f"Top high-fit leads:\n{top_leads_text if top_leads_text else '- None'}\n"
        )

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email
    msg.set_content(body)

    if csv_path and os.path.exists(csv_path):
        with open(csv_path, "rb") as f:
            msg.add_attachment(f.read(), maintype="text", subtype="csv", filename=os.path.basename(csv_path))

    with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
        server.starttls()
        if smtp_username:
            server.login(smtp_username, smtp_password)
        server.send_message(msg)


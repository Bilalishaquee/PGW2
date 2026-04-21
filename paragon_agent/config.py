from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    db_path: str = os.getenv("PARAGON_DB_PATH", "./data/paragon_leads.db")
    timezone: str = os.getenv("PARAGON_TIMEZONE", "America/New_York")
    min_fit_score: int = int(os.getenv("PARAGON_MIN_FIT_SCORE", "60"))
    high_fit_score: int = int(os.getenv("PARAGON_HIGH_FIT_SCORE", "80"))
    max_results_per_query: int = int(os.getenv("MAX_RESULTS_PER_QUERY", "10"))
    max_leads_per_run: int = int(os.getenv("MAX_LEADS_PER_RUN", "200"))
    require_contact_for_save: bool = os.getenv("REQUIRE_CONTACT_FOR_SAVE", "true").lower() in {"1", "true", "yes"}
    require_email_for_b2b: bool = os.getenv("REQUIRE_EMAIL_FOR_B2B", "false").lower() in {"1", "true", "yes"}

    serpapi_key: str = os.getenv("SERPAPI_KEY", "")
    bing_api_key: str = os.getenv("BING_API_KEY", "")

    smtp_host: str = os.getenv("SMTP_HOST", "")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    report_from_email: str = os.getenv("REPORT_FROM_EMAIL", "")
    report_to_email: str = os.getenv("REPORT_TO_EMAIL", "")


settings = Settings()


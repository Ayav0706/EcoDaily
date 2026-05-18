import asyncio
import logging
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv

from src import Newsletter
from src.fetch_news import fetch_all_levels
from src.generate_content import enrich_level
from src.render_email import render
from src.send_email import send

DAYS_ES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MONTHS_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def date_es(dt: datetime) -> str:
    return f"{DAYS_ES[dt.weekday()]}, {dt.day} de {MONTHS_ES[dt.month - 1]} de {dt.year}"


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        logging.critical("Required environment variable %s is not set.", name)
        sys.exit(1)
    return value


def main() -> None:
    load_dotenv()

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger(__name__)

    gemini_api_key = _require_env("GEMINI_API_KEY")
    resend_api_key = _require_env("RESEND_API_KEY")
    recipient_email = _require_env("RECIPIENT_EMAIL")
    from_email = _require_env("FROM_EMAIL")
    from_name = os.getenv("FROM_NAME", "EconoDaily")

    now = datetime.now(timezone.utc)
    date_str = date_es(now)
    generated_at = now.isoformat()

    logger.info("Starting EconoDaily pipeline for %s", date_str)

    try:
        levels = fetch_all_levels()
        logger.info("Fetched %d levels", len(levels))
    except Exception as exc:
        logger.critical("Failed to fetch news levels: %s", exc)
        sys.exit(1)

    enriched_levels = []
    for level in levels:
        try:
            enriched = asyncio.run(enrich_level(level, date_str, gemini_api_key))
            enriched_levels.append(enriched)
        except Exception as exc:
            logger.error("Enrichment failed for level %s, using RSS fallback: %s", level.level, exc)
            enriched_levels.append(level)

    newsletter = Newsletter(
        date=date_str,
        levels=enriched_levels,
        generated_at=generated_at,
    )

    try:
        html = render(newsletter)
        logger.info("Email rendered, %d chars", len(html))
    except Exception as exc:
        logger.critical("Failed to render email: %s", exc)
        sys.exit(1)

    subject = f"🗞️ EconoDaily — {date_str}"
    success = send(
        html=html,
        subject=subject,
        api_key=resend_api_key,
        to=recipient_email,
        from_email=from_email,
        from_name=from_name,
    )

    if success:
        logger.info("Pipeline completed successfully.")
        sys.exit(0)
    else:
        logger.error("Pipeline completed but email delivery failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()

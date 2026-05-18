import asyncio
import logging
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv

from src import Newsletter, NewsLevel
from src.fetch_news import fetch_all_levels
from src.generate_content import enrich_level
from src.render_email import render
from src.send_email import send

_DAYS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
_MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
           "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def _date_es(dt: datetime) -> str:
    return f"{_DAYS[dt.weekday()]}, {dt.day} de {_MONTHS[dt.month - 1]} de {dt.year}"


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        logging.critical("Missing required env var: %s", name)
        sys.exit(1)
    return value


def _enrich_all(levels: list[NewsLevel], date: str, api_key: str) -> list[NewsLevel]:
    result = []
    for level in levels:
        try:
            result.append(asyncio.run(enrich_level(level, date, api_key)))
        except Exception as exc:
            logging.error("Enrichment failed for %s, using RSS fallback: %s", level.level, exc)
            result.append(level)
    return result


def main() -> None:
    load_dotenv()
    logging.basicConfig(
        level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    now = datetime.now(timezone.utc)
    date_str = _date_es(now)
    logging.info("EconoDaily pipeline — %s", date_str)
    try:
        levels = fetch_all_levels()
    except Exception as exc:
        logging.critical("fetch_all_levels failed: %s", exc)
        sys.exit(1)
    newsletter = Newsletter(
        date=date_str,
        levels=_enrich_all(levels, date_str, _require_env("GEMINI_API_KEY")),
        generated_at=now.isoformat(),
    )
    try:
        html = render(newsletter)
    except Exception as exc:
        logging.critical("render failed: %s", exc)
        sys.exit(1)
    ok = send(html, f"🗞️ EconoDaily — {date_str}", _require_env("RESEND_API_KEY"),
              _require_env("RECIPIENT_EMAIL"), _require_env("FROM_EMAIL"),
              os.getenv("FROM_NAME", "EconoDaily"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

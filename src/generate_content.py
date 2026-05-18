import asyncio
import json
import logging
import re

import httpx

from src import NewsItem, NewsLevel

logger = logging.getLogger(__name__)

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
)

_SYSTEM = (
    "Eres un economista redactor de boletines diarios. "
    "Recibes noticias crudas y produces resúmenes ejecutivos en español, "
    "estilo académico riguroso, sin inventar datos. "
    'Si una noticia no tiene suficiente detalle, di "Datos insuficientes para análisis".'
)

_PROMPT = """Fecha: {date}
Noticias del nivel {level} ({label}):
{raw_items_json}

Redacta para cada noticia:
- Titular (máximo 12 palabras)
- Resumen (máximo 3 oraciones, datos concretos)
- "Por qué importa" (máximo 2 oraciones, enfoque económico)

Responde SOLO en JSON con esta estructura:
[{{"title": "...", "summary": "...", "why_it_matters": "..."}}]"""


def build_prompt(level: NewsLevel, date: str) -> str:
    raw_items = [
        {"title": item.title, "summary": item.summary, "url": item.url}
        for item in level.items
    ]
    return _PROMPT.format(
        date=date,
        level=level.level,
        label=level.label,
        raw_items_json=json.dumps(raw_items, ensure_ascii=False, indent=2),
    )


async def call_gemini(prompt: str, api_key: str) -> str:
    body = {
        "system_instruction": {"parts": [{"text": _SYSTEM}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 2048},
    }
    url = f"{GEMINI_URL}?key={api_key}"
    delays = [2, 4]
    async with httpx.AsyncClient(timeout=30.0) as client:
        for attempt in range(3):
            response = await client.post(url, json=body)
            if response.status_code == 429 and attempt < 2:
                wait = delays[attempt]
                logger.warning("Gemini 429 rate limit, retrying in %ss", wait)
                await asyncio.sleep(wait)
                continue
            response.raise_for_status()
            return response.text
    return ""


def parse_gemini_response(raw: str) -> list[dict]:
    """Extract JSON array from Gemini response, handling markdown code blocks."""
    # Strip markdown fences if present
    text = raw
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        text = match.group(1)
    else:
        # Try to extract a JSON array directly
        match = re.search(r"\[[\s\S]*\]", text)
        if match:
            text = match.group(0)
    try:
        result = json.loads(text.strip())
        if isinstance(result, list):
            return result
        return []
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("Failed to parse Gemini response: %s", exc)
        return []


def _apply_enrichment(original: list[NewsItem], enriched: list[dict]) -> list[NewsItem]:
    result = []
    for i, item in enumerate(original):
        if i < len(enriched):
            d = enriched[i]
            result.append(NewsItem(
                title=d.get("title", item.title) or item.title,
                summary=d.get("summary", item.summary) or item.summary,
                url=item.url,
                source=item.source,
                published=item.published,
                why_it_matters=d.get("why_it_matters", "") or "",
            ))
        else:
            result.append(item)
    return result


async def enrich_level(level: NewsLevel, date: str, api_key: str) -> NewsLevel:
    if not level.items:
        return level
    try:
        enriched = parse_gemini_response(await call_gemini(build_prompt(level, date), api_key))
        if not enriched:
            logger.warning("Empty Gemini response for %s — RSS fallback", level.level)
            return level
        return NewsLevel(level=level.level, emoji=level.emoji, label=level.label,
                         items=_apply_enrichment(level.items, enriched))
    except Exception as exc:
        logger.error("Gemini enrichment failed for %s: %s", level.level, exc)
        return level

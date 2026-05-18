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

SYSTEM_INSTRUCTION = (
    "Eres un economista redactor de boletines diarios. "
    "Recibes noticias crudas y produces resúmenes ejecutivos en español, "
    "estilo académico riguroso, sin inventar datos. "
    "Si una noticia no tiene suficiente detalle, di \"Datos insuficientes para análisis\"."
)

PROMPT_TEMPLATE = """{system}

Fecha: {date}
Noticias del nivel {level} ({label}):
{raw_items_json}

Redacta para cada noticia:
- Titular (máximo 12 palabras)
- Resumen (máximo 3 oraciones, datos concretos)
- "Por qué importa" (máximo 2 oraciones, enfoque económico)

Responde SOLO en JSON con esta estructura:
[{{"title": "...", "summary": "...", "why_it_matters": "..."}}]"""


def build_prompt(level: NewsLevel, date: str) -> str:
    """Build the Gemini prompt for a given level."""
    raw_items = [
        {"title": item.title, "summary": item.summary, "url": item.url}
        for item in level.items
    ]
    return PROMPT_TEMPLATE.format(
        system=SYSTEM_INSTRUCTION,
        date=date,
        level=level.level,
        label=level.label,
        raw_items_json=json.dumps(raw_items, ensure_ascii=False, indent=2),
    )


async def call_gemini(prompt: str, api_key: str) -> str:
    """Call the Gemini REST API with exponential backoff on HTTP 429."""
    body = {
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


async def enrich_level(level: NewsLevel, date: str, api_key: str) -> NewsLevel:
    """Enrich level items with Gemini-generated content. Falls back to original on error."""
    if not level.items:
        return level
    try:
        prompt = build_prompt(level, date)
        raw = await call_gemini(prompt, api_key)
        enriched = parse_gemini_response(raw)
        if not enriched:
            logger.warning("Empty Gemini response for level %s, using RSS fallback", level.level)
            return level

        new_items: list[NewsItem] = []
        for i, item in enumerate(level.items):
            if i < len(enriched):
                data = enriched[i]
                new_items.append(NewsItem(
                    title=data.get("title", item.title) or item.title,
                    summary=data.get("summary", item.summary) or item.summary,
                    url=item.url,
                    source=item.source,
                    published=item.published,
                    why_it_matters=data.get("why_it_matters", "") or "",
                ))
            else:
                new_items.append(item)

        return NewsLevel(
            level=level.level,
            emoji=level.emoji,
            label=level.label,
            items=new_items,
        )
    except Exception as exc:
        logger.error("Gemini enrichment failed for level %s: %s", level.level, exc)
        return level

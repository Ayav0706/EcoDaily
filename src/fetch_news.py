import logging
import socket
from datetime import datetime, timezone

import bleach
import feedparser

from src import NewsItem, NewsLevel

logger = logging.getLogger(__name__)

SOURCES: dict[str, list[str]] = {
    "macro": [
        "https://www.imf.org/en/News/rss",
        "https://feeds.worldbank.org/worldbank/news/press-releases",
        "https://www.bis.org/rss/press.rss",
        "https://www.oecd.org/newsroom/rss/",
    ],
    "meso": [
        "https://www.cepal.org/es/rss",
        "https://www.iadb.org/rss/news.cfm",
        "https://www.americaeconomia.com/rss.xml",
    ],
    "micro": [
        "https://www.bce.fin.ec/rss",
        "https://www.eluniverso.com/rss/economia/",
        "https://www.elcomercio.com/rss/economia.xml",
        "https://www.primicias.ec/rss/economia",
    ],
}

LEVEL_META: dict[str, dict[str, str]] = {
    "macro": {"emoji": "🌍", "label": "Economía Global"},
    "meso":  {"emoji": "🌎", "label": "Latinoamérica"},
    "micro": {"emoji": "🇪🇨", "label": "Ecuador"},
}


def _clean(text: str) -> str:
    """Strip HTML tags and sanitize RSS-sourced text."""
    return bleach.clean(text, tags=[], strip=True).strip()


def fetch_feed(url: str) -> list[NewsItem]:
    """Fetch a single RSS feed and return up to 10 NewsItems."""
    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(15)
    try:
        feed = feedparser.parse(url)
        items: list[NewsItem] = []
        for entry in feed.entries[:10]:
            title = _clean(getattr(entry, "title", "") or "")
            summary = _clean(getattr(entry, "summary", "") or getattr(entry, "description", "") or "")
            link = getattr(entry, "link", "") or ""
            source = getattr(feed.feed, "title", url) or url
            published_parsed = getattr(entry, "published_parsed", None)
            if published_parsed:
                published = datetime(*published_parsed[:6], tzinfo=timezone.utc).isoformat()
            else:
                published = datetime.now(timezone.utc).isoformat()
            items.append(NewsItem(
                title=title,
                summary=summary,
                url=link,
                source=_clean(source),
                published=published,
            ))
        return items
    except Exception as exc:
        logger.warning("Failed to fetch feed %s: %s", url, exc)
        return []
    finally:
        socket.setdefaulttimeout(old_timeout)


def fetch_level(level: str) -> NewsLevel:
    """Fetch all feeds for a level, combine, sort by published desc, keep top 5."""
    meta = LEVEL_META[level]
    all_items: list[NewsItem] = []
    for url in SOURCES[level]:
        all_items.extend(fetch_feed(url))

    all_items.sort(key=lambda x: x.published, reverse=True)
    top_items = all_items[:5]

    return NewsLevel(
        level=level,
        emoji=meta["emoji"],
        label=meta["label"],
        items=top_items,
    )


def fetch_all_levels() -> list[NewsLevel]:
    """Fetch all three levels: macro, meso, micro."""
    return [fetch_level(lvl) for lvl in ("macro", "meso", "micro")]

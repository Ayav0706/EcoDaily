from dataclasses import dataclass, field


@dataclass
class NewsItem:
    title: str
    summary: str
    url: str
    source: str
    published: str  # ISO 8601
    why_it_matters: str = ""


@dataclass
class NewsLevel:
    level: str          # "macro" | "meso" | "micro"
    emoji: str          # "🌍" | "🌎" | "🇪🇨"
    label: str          # "Economía Global" | "Latinoamérica" | "Ecuador"
    items: list[NewsItem] = field(default_factory=list)


@dataclass
class Newsletter:
    date: str           # "Lunes, 18 de mayo de 2026"
    levels: list[NewsLevel]
    generated_at: str   # ISO 8601 timestamp

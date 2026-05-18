# Glossary

Key terms used in the EconoDaily project.

---

**RSS (Really Simple Syndication)**
A web feed format that allows content publishers to syndicate data automatically.
EconoDaily uses RSS feeds from IMF, World Bank, BIS, OECD, CEPAL, IDB, BCE, and local Ecuadorian
news outlets to gather economic news.

**LLM (Large Language Model)**
A machine learning model trained on large text datasets capable of generating human-quality text.
EconoDaily uses Gemini 2.5 Flash to enrich RSS summaries with professional economic analysis.

**Gemini**
Google's large language model family. EconoDaily uses **Gemini 2.5 Flash** via the REST API
at `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent`.

**Resend**
A developer-focused email API service. EconoDaily uses the Resend Python SDK v2 to deliver the
rendered HTML newsletter to the recipient inbox.

**premailer**
A Python library that inlines CSS styles into HTML tags, making them compatible with email clients
(which strip `<style>` blocks). Used in `src/render_email.py`.

**Jinja2**
A Python templating engine. EconoDaily uses it to render `templates/newsletter.html.j2` into
full HTML with data substituted from `Newsletter` dataclass instances. `autoescape=True` is
always enabled to prevent XSS from RSS content.

**NewsItem**
A dataclass (`src/__init__.py`) representing a single news article: title, summary, URL, source,
published timestamp, and optional `why_it_matters` enrichment from Gemini.

**NewsLevel**
A dataclass grouping a list of `NewsItem` objects at a given geographic/economic scope.
Contains `level`, `emoji`, `label`, and `items`.

**Newsletter**
The top-level dataclass passed to the Jinja2 template. Contains `date` (Spanish formatted),
`levels` (list of `NewsLevel`), and `generated_at` (ISO 8601 timestamp).

**macro level**
The global economic scope. Emoji: 🌍. Label: "Economía Global". Sources: IMF, World Bank, BIS, OECD.

**meso level**
The Latin American regional scope. Emoji: 🌎. Label: "Latinoamérica". Sources: CEPAL, IDB,
AmericaEconomía.

**micro level**
The Ecuador-specific scope. Emoji: 🇪🇨. Label: "Ecuador". Sources: BCE, El Universo,
El Comercio, Primicias.

**feedparser**
A Python library for parsing RSS and Atom feeds. Used in `src/fetch_news.py` with a 15-second
socket timeout.

**bleach**
A Python HTML sanitization library. Used in `src/fetch_news.py` to strip HTML tags and sanitize
all RSS-sourced text before it is stored in `NewsItem` fields.

**GitHub Actions**
CI/CD platform provided by GitHub. EconoDaily uses a scheduled workflow
(`.github/workflows/daily_newsletter.yml`) to run the pipeline Monday–Friday at 11:00 UTC
(06:00 Ecuador time).

**pip-audit**
A tool that checks Python packages for known security vulnerabilities. Used only in the
GitHub Actions CI workflow (`pip install pip-audit && pip-audit -r requirements.txt`);
not listed in `requirements.txt`.

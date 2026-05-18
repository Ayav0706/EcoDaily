# Changelog

All notable changes to EconoDaily are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.1.0] — 2026-05-18

### Added
- `src/__init__.py` — dataclasses: `NewsItem`, `NewsLevel`, `Newsletter`
- `src/fetch_news.py` — RSS feed fetching with bleach sanitization; supports macro/meso/micro levels
- `src/generate_content.py` — Gemini 2.5 Flash enrichment via REST API; async with retry on HTTP 429
- `src/render_email.py` — Jinja2 HTML email rendering with premailer CSS inlining
- `src/send_email.py` — email delivery via Resend Python SDK v2
- `src/main.py` — orchestration entry point (≤80 LOC)
- `templates/newsletter.html.j2` — table-based HTML email template with macro/meso/micro sections
- `tests/test_fetch_news.py` — unit tests for RSS fetching
- `tests/test_generate_content.py` — unit tests for Gemini prompt building, response parsing, HTTP retries
- `tests/test_render_email.py` — unit tests for Jinja2 rendering
- `.github/workflows/daily_newsletter.yml` — GitHub Actions schedule (Mon–Fri 11:00 UTC)
- `requirements.txt` — pinned Python dependencies
- `.env.example` — environment variable template
- `.gitignore` — excludes .env, __pycache__, build artifacts
- `CLAUDE.md` — AI agent instructions
- `.ai-memory/` — session memory files for AI continuity

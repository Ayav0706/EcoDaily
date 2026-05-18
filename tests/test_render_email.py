"""Tests for src/render_email.py"""
import pytest

from src import NewsItem, NewsLevel, Newsletter
from src.render_email import render


def _make_sample_newsletter() -> Newsletter:
    """Create a sample Newsletter for testing."""
    macro_items = [
        NewsItem(
            title="Global Growth Slows",
            summary="World Bank reports slowdown in global economic growth.",
            url="https://worldbank.org/1",
            source="World Bank",
            published="2026-05-18T10:00:00+00:00",
            why_it_matters="Impacts trade and investment flows.",
        )
    ]
    meso_items = [
        NewsItem(
            title="Latin America Recovery",
            summary="CEPAL sees modest recovery across the region.",
            url="https://cepal.org/1",
            source="CEPAL",
            published="2026-05-18T09:00:00+00:00",
            why_it_matters="Regional economies stabilizing post-shock.",
        )
    ]
    micro_items = [
        NewsItem(
            title="Ecuador GDP Beats Forecast",
            summary="BCE reports Q1 GDP growth of 2.1%, above expectations.",
            url="https://bce.fin.ec/1",
            source="BCE",
            published="2026-05-18T08:00:00+00:00",
            why_it_matters="Positive signal for domestic investment.",
        )
    ]

    levels = [
        NewsLevel(level="macro", emoji="🌍", label="Economía Global", items=macro_items),
        NewsLevel(level="meso", emoji="🌎", label="Latinoamérica", items=meso_items),
        NewsLevel(level="micro", emoji="🇪🇨", label="Ecuador", items=micro_items),
    ]

    return Newsletter(
        date="Lunes, 18 de mayo de 2026",
        levels=levels,
        generated_at="2026-05-18T11:00:00+00:00",
    )


class TestRender:
    def test_returns_html_string(self):
        """render() returns a non-empty string."""
        newsletter = _make_sample_newsletter()
        html = render(newsletter)
        assert isinstance(html, str)
        assert len(html) > 0

    def test_output_has_minimum_length(self):
        """render() returns HTML with at least 1000 characters."""
        newsletter = _make_sample_newsletter()
        html = render(newsletter)
        assert len(html) >= 1000

    def test_contains_econodaily(self):
        """render() output contains 'EconoDaily'."""
        newsletter = _make_sample_newsletter()
        html = render(newsletter)
        assert "EconoDaily" in html

    def test_contains_all_level_labels(self):
        """render() output contains all three level labels."""
        newsletter = _make_sample_newsletter()
        html = render(newsletter)
        assert "Economía Global" in html
        assert "Latinoamérica" in html
        assert "Ecuador" in html

    def test_contains_newsletter_date(self):
        """render() includes the newsletter date."""
        newsletter = _make_sample_newsletter()
        html = render(newsletter)
        assert "Lunes, 18 de mayo de 2026" in html

    def test_contains_item_titles(self):
        """render() includes news item titles."""
        newsletter = _make_sample_newsletter()
        html = render(newsletter)
        assert "Global Growth Slows" in html

    def test_contains_why_it_matters(self):
        """render() includes 'Por qué importa' section when present."""
        newsletter = _make_sample_newsletter()
        html = render(newsletter)
        assert "Por qué importa" in html

    def test_output_is_html(self):
        """render() returns valid HTML with doctype."""
        newsletter = _make_sample_newsletter()
        html = render(newsletter)
        assert "<!DOCTYPE html>" in html or "<html" in html

    def test_empty_levels_renders_gracefully(self):
        """render() handles NewsLevel with no items without crashing."""
        levels = [
            NewsLevel(level="macro", emoji="🌍", label="Economía Global", items=[]),
            NewsLevel(level="meso", emoji="🌎", label="Latinoamérica", items=[]),
            NewsLevel(level="micro", emoji="🇪🇨", label="Ecuador", items=[]),
        ]
        newsletter = Newsletter(
            date="Lunes, 18 de mayo de 2026",
            levels=levels,
            generated_at="2026-05-18T11:00:00+00:00",
        )
        html = render(newsletter)
        assert isinstance(html, str)
        assert len(html) > 0

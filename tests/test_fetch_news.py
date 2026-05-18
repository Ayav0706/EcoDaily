"""Tests for src/fetch_news.py"""
from unittest.mock import MagicMock, patch

import pytest

from src import NewsItem, NewsLevel
from src.fetch_news import fetch_all_levels, fetch_feed, fetch_level


def _make_entry(title="Test Title", summary="Test Summary", link="https://example.com", published_parsed=None):
    entry = MagicMock()
    entry.title = title
    entry.summary = summary
    entry.description = summary
    entry.link = link
    entry.published_parsed = published_parsed
    return entry


def _make_feed(entries, feed_title="Test Feed"):
    feed_obj = MagicMock()
    feed_obj.title = feed_title
    parsed = MagicMock()
    parsed.entries = entries
    parsed.feed = feed_obj
    return parsed


class TestFetchFeed:
    def test_returns_news_item_list(self):
        """fetch_feed returns a list of NewsItems for a valid feed."""
        entry = _make_entry(title="Economy Grows", summary="GDP rose 2%", link="https://example.com/1")
        fake_feed = _make_feed([entry])
        with patch("src.fetch_news.feedparser.parse", return_value=fake_feed):
            items = fetch_feed("https://example.com/rss")
        assert isinstance(items, list)
        assert len(items) == 1
        assert isinstance(items[0], NewsItem)
        assert items[0].title == "Economy Grows"
        assert items[0].summary == "GDP rose 2%"
        assert items[0].url == "https://example.com/1"

    def test_returns_empty_on_exception(self):
        """fetch_feed returns [] when feedparser raises an exception."""
        with patch("src.fetch_news.feedparser.parse", side_effect=Exception("network error")):
            items = fetch_feed("https://example.com/bad-rss")
        assert items == []

    def test_limits_to_ten_items(self):
        """fetch_feed returns at most 10 items."""
        entries = [_make_entry(title=f"Item {i}") for i in range(15)]
        fake_feed = _make_feed(entries)
        with patch("src.fetch_news.feedparser.parse", return_value=fake_feed):
            items = fetch_feed("https://example.com/rss")
        assert len(items) <= 10

    def test_handles_missing_fields(self):
        """fetch_feed handles entries with missing title/summary gracefully."""
        entry = MagicMock()
        entry.title = None
        entry.summary = None
        entry.description = None
        entry.link = ""
        entry.published_parsed = None
        fake_feed = _make_feed([entry])
        with patch("src.fetch_news.feedparser.parse", return_value=fake_feed):
            items = fetch_feed("https://example.com/rss")
        assert isinstance(items, list)


class TestFetchLevel:
    def test_returns_news_level_with_correct_metadata_macro(self):
        """fetch_level returns NewsLevel with correct emoji and label for macro."""
        entry = _make_entry(title="IMF Report")
        fake_feed = _make_feed([entry])
        with patch("src.fetch_news.feedparser.parse", return_value=fake_feed):
            level = fetch_level("macro")
        assert isinstance(level, NewsLevel)
        assert level.level == "macro"
        assert level.emoji == "🌍"
        assert level.label == "Economía Global"

    def test_returns_news_level_with_correct_metadata_meso(self):
        """fetch_level returns NewsLevel with correct metadata for meso."""
        entry = _make_entry(title="CEPAL Report")
        fake_feed = _make_feed([entry])
        with patch("src.fetch_news.feedparser.parse", return_value=fake_feed):
            level = fetch_level("meso")
        assert level.emoji == "🌎"
        assert level.label == "Latinoamérica"

    def test_returns_news_level_with_correct_metadata_micro(self):
        """fetch_level returns NewsLevel with correct metadata for micro."""
        entry = _make_entry(title="BCE Report")
        fake_feed = _make_feed([entry])
        with patch("src.fetch_news.feedparser.parse", return_value=fake_feed):
            level = fetch_level("micro")
        assert level.emoji == "🇪🇨"
        assert level.label == "Ecuador"

    def test_keeps_top_5_items(self):
        """fetch_level keeps at most 5 items."""
        entries = [_make_entry(title=f"Item {i}") for i in range(8)]
        fake_feed = _make_feed(entries)
        with patch("src.fetch_news.feedparser.parse", return_value=fake_feed):
            level = fetch_level("macro")
        assert len(level.items) <= 5


class TestFetchAllLevels:
    def test_returns_three_levels(self):
        """fetch_all_levels returns exactly 3 NewsLevels."""
        entry = _make_entry()
        fake_feed = _make_feed([entry])
        with patch("src.fetch_news.feedparser.parse", return_value=fake_feed):
            levels = fetch_all_levels()
        assert len(levels) == 3
        level_names = [lvl.level for lvl in levels]
        assert "macro" in level_names
        assert "meso" in level_names
        assert "micro" in level_names

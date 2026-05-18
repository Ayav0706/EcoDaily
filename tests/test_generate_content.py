"""Tests for src/generate_content.py"""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src import NewsItem, NewsLevel
from src.generate_content import build_prompt, parse_gemini_response


def _make_level(level="macro", emoji="🌍", label="Economía Global") -> NewsLevel:
    items = [
        NewsItem(
            title="Global GDP Slows",
            summary="World economic growth slows to 2.8% in Q1.",
            url="https://example.com/1",
            source="IMF",
            published="2026-05-18T10:00:00+00:00",
        ),
        NewsItem(
            title="Trade Tensions Rise",
            summary="US-China trade dispute escalates.",
            url="https://example.com/2",
            source="World Bank",
            published="2026-05-18T09:00:00+00:00",
        ),
    ]
    return NewsLevel(level=level, emoji=emoji, label=label, items=items)


class TestBuildPrompt:
    def test_contains_level_name(self):
        """build_prompt includes the level name."""
        level = _make_level()
        prompt = build_prompt(level, "Lunes, 18 de mayo de 2026")
        assert "macro" in prompt

    def test_contains_date(self):
        """build_prompt includes the provided date."""
        level = _make_level()
        date = "Lunes, 18 de mayo de 2026"
        prompt = build_prompt(level, date)
        assert date in prompt

    def test_contains_label(self):
        """build_prompt includes the level label."""
        level = _make_level()
        prompt = build_prompt(level, "2026-05-18")
        assert "Economía Global" in prompt

    def test_contains_item_titles(self):
        """build_prompt includes item titles in the JSON."""
        level = _make_level()
        prompt = build_prompt(level, "2026-05-18")
        assert "Global GDP Slows" in prompt

    def test_contains_json_instruction(self):
        """build_prompt asks for JSON response."""
        level = _make_level()
        prompt = build_prompt(level, "2026-05-18")
        assert "JSON" in prompt


class TestParseGeminiResponse:
    def test_handles_valid_json_array(self):
        """parse_gemini_response returns list of dicts for valid JSON."""
        raw = json.dumps([
            {"title": "Test", "summary": "Summary text", "why_it_matters": "Important."}
        ])
        result = parse_gemini_response(raw)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["title"] == "Test"

    def test_handles_markdown_code_block(self):
        """parse_gemini_response strips ```json ... ``` fences."""
        data = [{"title": "T", "summary": "S", "why_it_matters": "W"}]
        raw = f"```json\n{json.dumps(data)}\n```"
        result = parse_gemini_response(raw)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["title"] == "T"

    def test_handles_markdown_code_block_no_lang(self):
        """parse_gemini_response strips ``` ... ``` fences without json tag."""
        data = [{"title": "X", "summary": "Y", "why_it_matters": "Z"}]
        raw = f"```\n{json.dumps(data)}\n```"
        result = parse_gemini_response(raw)
        assert isinstance(result, list)
        assert len(result) == 1

    def test_returns_empty_on_invalid_json(self):
        """parse_gemini_response returns [] when JSON is invalid."""
        result = parse_gemini_response("this is not json at all {broken}")
        assert result == []

    def test_returns_empty_on_empty_string(self):
        """parse_gemini_response returns [] for empty input."""
        result = parse_gemini_response("")
        assert result == []

    def test_returns_empty_on_non_array_json(self):
        """parse_gemini_response returns [] when response is a JSON object, not array."""
        raw = json.dumps({"title": "T", "summary": "S"})
        result = parse_gemini_response(raw)
        assert result == []

    def test_handles_multiple_items(self):
        """parse_gemini_response handles multiple items in array."""
        data = [
            {"title": "A", "summary": "SA", "why_it_matters": "WA"},
            {"title": "B", "summary": "SB", "why_it_matters": "WB"},
        ]
        raw = json.dumps(data)
        result = parse_gemini_response(raw)
        assert len(result) == 2
        assert result[1]["title"] == "B"


class TestCallGemini:
    @pytest.mark.asyncio
    async def test_call_gemini_returns_text_on_success(self):
        """call_gemini returns response text on HTTP 200."""
        from src.generate_content import call_gemini

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"candidates": []}'
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            result = await call_gemini("test prompt", "fake-api-key")

        assert result == '{"candidates": []}'

    @pytest.mark.asyncio
    async def test_call_gemini_retries_on_429(self):
        """call_gemini retries on HTTP 429 and succeeds on next attempt."""
        from src.generate_content import call_gemini

        mock_429 = MagicMock()
        mock_429.status_code = 429
        mock_429.raise_for_status = MagicMock()

        mock_200 = MagicMock()
        mock_200.status_code = 200
        mock_200.text = "ok"
        mock_200.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(side_effect=[mock_429, mock_200])
            mock_client_class.return_value = mock_client

            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await call_gemini("prompt", "fake-key")

        assert result == "ok"

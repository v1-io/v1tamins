"""Tests for Truth Social source module."""
import pytest
from unittest.mock import patch, MagicMock

from scripts.lib import truthsocial


class TestStripHtml:
    """Test HTML tag stripping."""

    def test_basic_paragraph(self):
        assert truthsocial._strip_html("<p>Hello world</p>") == "Hello world"

    def test_br_tags(self):
        assert truthsocial._strip_html("Line 1<br>Line 2") == "Line 1\nLine 2"
        assert truthsocial._strip_html("Line 1<br/>Line 2") == "Line 1\nLine 2"
        assert truthsocial._strip_html("Line 1<br />Line 2") == "Line 1\nLine 2"

    def test_nested_tags(self):
        assert truthsocial._strip_html("<p>Hello <a href='#'>world</a></p>") == "Hello world"

    def test_empty_string(self):
        assert truthsocial._strip_html("") == ""

    def test_no_tags(self):
        assert truthsocial._strip_html("plain text") == "plain text"

    def test_entities_preserved(self):
        assert truthsocial._strip_html("<p>&amp; test</p>") == "&amp; test"


class TestExtractCoreSubject:
    """Test query preprocessing."""

    def test_strips_question_prefix(self):
        assert truthsocial._extract_core_subject("what are people saying about tariffs") == "tariffs"

    def test_strips_noise_words(self):
        assert truthsocial._extract_core_subject("latest trending crypto news") == "crypto"

    def test_preserves_core_topic(self):
        assert truthsocial._extract_core_subject("tariffs") == "tariffs"

    def test_strips_trailing_punctuation(self):
        assert truthsocial._extract_core_subject("what is bitcoin?") == "bitcoin"


class TestParseDate:
    """Test date parsing from Mastodon status."""

    def test_iso_date(self):
        assert truthsocial._parse_date({"created_at": "2026-03-09T12:00:00.000Z"}) == "2026-03-09"

    def test_missing_date(self):
        assert truthsocial._parse_date({}) is None

    def test_short_date(self):
        assert truthsocial._parse_date({"created_at": "short"}) is None

    def test_none_value(self):
        assert truthsocial._parse_date({"created_at": None}) is None


class TestDepthConfig:
    """Test depth configuration."""

    def test_all_depths_exist(self):
        assert "quick" in truthsocial.DEPTH_CONFIG
        assert "default" in truthsocial.DEPTH_CONFIG
        assert "deep" in truthsocial.DEPTH_CONFIG

    def test_depth_ordering(self):
        assert truthsocial.DEPTH_CONFIG["quick"] < truthsocial.DEPTH_CONFIG["default"]
        assert truthsocial.DEPTH_CONFIG["default"] < truthsocial.DEPTH_CONFIG["deep"]


class TestSearchTruthSocial:
    """Test search function auth handling."""

    def test_no_config_returns_error(self):
        result = truthsocial.search_truthsocial("test", "2026-02-09", "2026-03-09")
        assert result["statuses"] == []
        assert "not configured" in result["error"]

    def test_empty_token_returns_error(self):
        result = truthsocial.search_truthsocial(
            "test", "2026-02-09", "2026-03-09",
            config={"TRUTHSOCIAL_TOKEN": ""},
        )
        assert result["statuses"] == []
        assert "not configured" in result["error"]

    @patch("scripts.lib.truthsocial.http.request")
    def test_401_returns_token_expired(self, mock_request):
        from scripts.lib.http import HTTPError
        mock_request.side_effect = HTTPError("Unauthorized", status_code=401)
        result = truthsocial.search_truthsocial(
            "test", "2026-02-09", "2026-03-09",
            config={"TRUTHSOCIAL_TOKEN": "expired_token"},
        )
        assert result["statuses"] == []
        assert "expired" in result["error"]

    @patch("scripts.lib.truthsocial.http.request")
    def test_403_returns_access_denied(self, mock_request):
        from scripts.lib.http import HTTPError
        mock_request.side_effect = HTTPError("Forbidden", status_code=403)
        result = truthsocial.search_truthsocial(
            "test", "2026-02-09", "2026-03-09",
            config={"TRUTHSOCIAL_TOKEN": "blocked_token"},
        )
        assert result["statuses"] == []
        assert "Cloudflare" in result["error"]

    @patch("scripts.lib.truthsocial.http.request")
    def test_429_returns_rate_limited(self, mock_request):
        from scripts.lib.http import HTTPError
        mock_request.side_effect = HTTPError("Too Many Requests", status_code=429)
        result = truthsocial.search_truthsocial(
            "test", "2026-02-09", "2026-03-09",
            config={"TRUTHSOCIAL_TOKEN": "rate_limited_token"},
        )
        assert result["statuses"] == []
        assert "rate limited" in result["error"]

    @patch("scripts.lib.truthsocial.http.request")
    def test_successful_search(self, mock_request):
        mock_request.return_value = {
            "statuses": [
                {
                    "content": "<p>Test post about tariffs</p>",
                    "created_at": "2026-03-09T12:00:00.000Z",
                    "url": "https://truthsocial.com/@user/123",
                    "account": {"acct": "user", "display_name": "Test User"},
                    "favourites_count": 10,
                    "reblogs_count": 5,
                    "replies_count": 3,
                }
            ]
        }
        result = truthsocial.search_truthsocial(
            "tariffs", "2026-02-09", "2026-03-09",
            config={"TRUTHSOCIAL_TOKEN": "valid_token"},
        )
        assert len(result["statuses"]) == 1
        # Verify bearer token was passed
        call_args = mock_request.call_args
        assert call_args[1]["headers"]["Authorization"] == "Bearer valid_token"


class TestParseTruthSocialResponse:
    """Test response parsing."""

    def test_basic_post(self):
        response = {
            "statuses": [
                {
                    "content": "<p>Hello from Truth Social</p>",
                    "created_at": "2026-03-09T12:00:00.000Z",
                    "url": "https://truthsocial.com/@testuser/456",
                    "account": {"acct": "testuser", "display_name": "Test User"},
                    "favourites_count": 100,
                    "reblogs_count": 50,
                    "replies_count": 25,
                }
            ]
        }
        items = truthsocial.parse_truthsocial_response(response)
        assert len(items) == 1
        item = items[0]
        assert item["handle"] == "testuser"
        assert item["display_name"] == "Test User"
        assert item["text"] == "Hello from Truth Social"  # HTML stripped
        assert item["url"] == "https://truthsocial.com/@testuser/456"
        assert item["date"] == "2026-03-09"
        assert item["engagement"]["likes"] == 100
        assert item["engagement"]["reposts"] == 50
        assert item["engagement"]["replies"] == 25
        assert item["relevance"] > 0

    def test_empty_response(self):
        items = truthsocial.parse_truthsocial_response({"statuses": []})
        assert items == []

    def test_missing_fields(self):
        response = {
            "statuses": [
                {
                    "content": "",
                    "account": {},
                }
            ]
        }
        items = truthsocial.parse_truthsocial_response(response)
        assert len(items) == 1
        assert items[0]["handle"] == ""
        assert items[0]["text"] == ""
        assert items[0]["engagement"]["likes"] == 0

    def test_relevance_ordering(self):
        response = {
            "statuses": [
                {"content": "<p>First</p>", "account": {"acct": "a"}, "favourites_count": 10, "reblogs_count": 0, "replies_count": 0},
                {"content": "<p>Second</p>", "account": {"acct": "b"}, "favourites_count": 5, "reblogs_count": 0, "replies_count": 0},
                {"content": "<p>Third</p>", "account": {"acct": "c"}, "favourites_count": 1, "reblogs_count": 0, "replies_count": 0},
            ]
        }
        items = truthsocial.parse_truthsocial_response(response)
        assert items[0]["relevance"] >= items[1]["relevance"]
        assert items[1]["relevance"] >= items[2]["relevance"]

    def test_html_stripping_in_parse(self):
        response = {
            "statuses": [
                {
                    "content": "<p>Hello <a href='https://example.com'>@user</a> check this out<br/>New line</p>",
                    "account": {"acct": "poster"},
                    "favourites_count": 0,
                    "reblogs_count": 0,
                    "replies_count": 0,
                }
            ]
        }
        items = truthsocial.parse_truthsocial_response(response)
        assert "<" not in items[0]["text"]
        assert ">" not in items[0]["text"]

"""Tests for bluesky module."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from lib import bluesky


class TestExtractCoreSubject(unittest.TestCase):
    def test_strips_prefix(self):
        result = bluesky._extract_core_subject("what are people saying about claude code")
        self.assertEqual(result, "claude code")

    def test_strips_noise(self):
        result = bluesky._extract_core_subject("latest trending news claude code")
        self.assertNotIn("latest", result)
        self.assertNotIn("trending", result)
        self.assertIn("claude", result)

    def test_preserves_core(self):
        result = bluesky._extract_core_subject("react native")
        self.assertEqual(result, "react native")


class TestParseDate(unittest.TestCase):
    def test_indexed_at_iso(self):
        item = {"indexedAt": "2024-06-15T12:00:00Z"}
        self.assertEqual(bluesky._parse_date(item), "2024-06-15")

    def test_created_at_iso(self):
        item = {"createdAt": "2024-03-01T08:30:00.000Z"}
        self.assertEqual(bluesky._parse_date(item), "2024-03-01")

    def test_indexed_at_preferred_over_created_at(self):
        item = {"indexedAt": "2024-06-15T12:00:00Z", "createdAt": "2024-06-14T12:00:00Z"}
        self.assertEqual(bluesky._parse_date(item), "2024-06-15")

    def test_none_returns_none(self):
        self.assertIsNone(bluesky._parse_date({}))

    def test_invalid_date_returns_none(self):
        self.assertIsNone(bluesky._parse_date({"indexedAt": "not-a-date"}))


class TestParseBlueskyResponse(unittest.TestCase):
    def test_basic_post(self):
        response = {
            "posts": [{
                "uri": "at://did:plc:abc123/app.bsky.feed.post/xyz789",
                "author": {"handle": "alice.bsky.social", "displayName": "Alice"},
                "record": {"text": "Hello world", "createdAt": "2024-06-15T12:00:00Z"},
                "indexedAt": "2024-06-15T12:01:00Z",
                "likeCount": 10,
                "repostCount": 5,
                "replyCount": 3,
                "quoteCount": 1,
            }]
        }
        items = bluesky.parse_bluesky_response(response)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["handle"], "alice.bsky.social")
        self.assertEqual(items[0]["display_name"], "Alice")
        self.assertEqual(items[0]["text"], "Hello world")
        self.assertEqual(items[0]["url"], "https://bsky.app/profile/alice.bsky.social/post/xyz789")
        self.assertEqual(items[0]["engagement"]["likes"], 10)
        self.assertEqual(items[0]["engagement"]["reposts"], 5)
        self.assertEqual(items[0]["date"], "2024-06-15")

    def test_empty_response(self):
        items = bluesky.parse_bluesky_response({})
        self.assertEqual(items, [])

    def test_missing_fields(self):
        response = {"posts": [{"uri": "", "author": {}, "record": {}}]}
        items = bluesky.parse_bluesky_response(response)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["handle"], "")
        self.assertEqual(items[0]["text"], "")

    def test_relevance_decreases_with_position(self):
        response = {"posts": [
            {"uri": f"at://did/app.bsky.feed.post/{i}", "author": {"handle": f"u{i}"}, "record": {"text": f"post {i}"}}
            for i in range(5)
        ]}
        items = bluesky.parse_bluesky_response(response)
        self.assertGreater(items[0]["relevance"], items[4]["relevance"])


class TestDepthConfig(unittest.TestCase):
    def test_all_depths_exist(self):
        for depth in ("quick", "default", "deep"):
            self.assertIn(depth, bluesky.DEPTH_CONFIG)

    def test_deep_has_more_results(self):
        quick = bluesky.DEPTH_CONFIG["quick"]
        deep = bluesky.DEPTH_CONFIG["deep"]
        self.assertGreater(deep, quick)


class TestCreateSession(unittest.TestCase):
    def setUp(self):
        bluesky._cached_token = None

    def tearDown(self):
        bluesky._cached_token = None

    @patch("lib.bluesky.http.request")
    def test_returns_token(self, mock_request):
        mock_request.return_value = {"accessJwt": "tok123", "refreshJwt": "ref456"}
        token = bluesky._create_session("user.bsky.social", "app-pw")
        self.assertEqual(token, "tok123")
        mock_request.assert_called_once()

    @patch("lib.bluesky.http.request")
    def test_caches_token(self, mock_request):
        mock_request.return_value = {"accessJwt": "tok123", "refreshJwt": "ref456"}
        bluesky._create_session("user.bsky.social", "app-pw")
        bluesky._create_session("user.bsky.social", "app-pw")
        mock_request.assert_called_once()  # Only one HTTP call

    @patch("lib.bluesky.http.request")
    def test_returns_none_on_failure(self, mock_request):
        mock_request.side_effect = Exception("connection refused")
        token = bluesky._create_session("user.bsky.social", "app-pw")
        self.assertIsNone(token)

    @patch("lib.bluesky.http.request")
    def test_returns_none_on_missing_jwt(self, mock_request):
        mock_request.return_value = {"did": "did:plc:abc"}
        token = bluesky._create_session("user.bsky.social", "app-pw")
        self.assertIsNone(token)


class TestSearchBlueskyAuth(unittest.TestCase):
    def setUp(self):
        bluesky._cached_token = None

    def tearDown(self):
        bluesky._cached_token = None

    def test_no_config_returns_error(self):
        result = bluesky.search_bluesky("test", "2026-01-01", "2026-03-09")
        self.assertEqual(result["posts"], [])
        self.assertIn("not configured", result["error"])

    def test_empty_config_returns_error(self):
        result = bluesky.search_bluesky("test", "2026-01-01", "2026-03-09", config={})
        self.assertEqual(result["posts"], [])
        self.assertIn("not configured", result["error"])

    @patch("lib.bluesky.http.request")
    def test_auth_failure_returns_error(self, mock_request):
        mock_request.side_effect = Exception("401 Unauthorized")
        config = {"BSKY_HANDLE": "user.bsky.social", "BSKY_APP_PASSWORD": "pw"}
        result = bluesky.search_bluesky("test", "2026-01-01", "2026-03-09", config=config)
        self.assertEqual(result["posts"], [])
        self.assertIn("auth failed", result["error"])

    @patch("lib.bluesky.http.request")
    def test_successful_search_passes_bearer(self, mock_request):
        # First call: createSession, second call: searchPosts
        mock_request.side_effect = [
            {"accessJwt": "tok123", "refreshJwt": "ref456"},
            {"posts": [{"uri": "at://did/app.bsky.feed.post/abc", "author": {"handle": "u1"}, "record": {"text": "hi"}}]},
        ]
        config = {"BSKY_HANDLE": "user.bsky.social", "BSKY_APP_PASSWORD": "pw"}
        result = bluesky.search_bluesky("test", "2026-01-01", "2026-03-09", config=config)
        self.assertEqual(len(result["posts"]), 1)
        # Verify the search call included the Bearer token
        search_call = mock_request.call_args_list[1]
        self.assertEqual(search_call.kwargs.get("headers", {}), {"Authorization": "Bearer tok123"})


if __name__ == "__main__":
    unittest.main()

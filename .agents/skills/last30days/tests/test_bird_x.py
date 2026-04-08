"""Tests for bird_x module."""

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib import bird_x


class TestExtractCoreSubject(unittest.TestCase):
    def test_strips_trending_noise(self):
        result = bird_x._extract_core_subject("trendiest Claude Code skills")
        self.assertNotIn("trendiest", result)
        self.assertIn("claude", result.lower())

    def test_strips_tool_noise(self):
        result = bird_x._extract_core_subject("best AI tools for coding")
        self.assertNotIn("tools", result)
        self.assertNotIn("best", result)

    def test_strips_skill_noise(self):
        result = bird_x._extract_core_subject("top claude code skills")
        self.assertNotIn("skills", result)
        self.assertNotIn("top", result)


class TestBirdSearchRetries(unittest.TestCase):
    def test_last_chance_retry_uses_strongest_token(self):
        """When shorter retry also returns 0, uses longest non-noise token."""
        empty = {"items": []}
        with mock.patch.object(bird_x, "_extract_core_subject", return_value="best codex skill plugin"), \
             mock.patch.object(bird_x, "parse_bird_response", return_value=[]), \
             mock.patch.object(bird_x, "_run_bird_search", return_value=empty) as run_mock:
            bird_x.search_x("best codex skill plugin", "2026-01-01", "2026-01-31", depth="quick")

        # Should try: original, shorter (2-word), last-chance (strongest token)
        self.assertEqual(run_mock.call_count, 3)
        queries = [call.args[0] for call in run_mock.call_args_list]
        # Last call should use "codex" (longest non-noise word)
        self.assertIn("codex", queries[2])

    def test_no_retry_when_first_query_has_results(self):
        """No retry when first query succeeds."""
        result = {"items": [{"id": "1"}]}
        with mock.patch.object(bird_x, "_extract_core_subject", return_value="nano banana"), \
             mock.patch.object(bird_x, "parse_bird_response", return_value=[{"id": "1"}]), \
             mock.patch.object(bird_x, "_run_bird_search", return_value=result) as run_mock:
            bird_x.search_x("nano banana prompting", "2026-01-01", "2026-01-31")

        self.assertEqual(run_mock.call_count, 1)


if __name__ == "__main__":
    unittest.main()

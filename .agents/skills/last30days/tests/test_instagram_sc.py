"""Tests for instagram.py — ScrapeCreators Instagram search module."""

import sys
import unittest
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib import instagram


class TestTokenize(unittest.TestCase):
    """Tests for _tokenize()."""

    def test_strips_stopwords(self):
        tokens = instagram._tokenize("how to use the AI tools")
        self.assertNotIn("how", tokens)
        self.assertNotIn("the", tokens)
        self.assertNotIn("to", tokens)

    def test_expands_synonyms(self):
        tokens = instagram._tokenize("ai tools")
        self.assertTrue("artificial" in tokens or "intelligence" in tokens)

    def test_removes_single_char(self):
        tokens = instagram._tokenize("a b c python")
        self.assertNotIn("a", tokens)
        self.assertNotIn("b", tokens)
        self.assertIn("python", tokens)

    def test_lowercases(self):
        tokens = instagram._tokenize("Python REACT")
        self.assertIn("python", tokens)
        self.assertIn("react", tokens)

    def test_strips_punctuation(self):
        tokens = instagram._tokenize("hello, world!")
        self.assertIn("hello", tokens)
        self.assertIn("world", tokens)


class TestComputeRelevance(unittest.TestCase):
    """Tests for _compute_relevance()."""

    def test_exact_match_high(self):
        rel = instagram._compute_relevance("claude code", "Claude Code tricks and tips")
        self.assertGreaterEqual(rel, 0.8)

    def test_partial_match_lower(self):
        rel = instagram._compute_relevance("claude code tips", "Best AI tools for coding")
        self.assertLess(rel, 0.5)

    def test_hashtag_boost(self):
        base = instagram._compute_relevance("claude code", "random video about stuff")
        boosted = instagram._compute_relevance("claude code", "random video about stuff", ["claudecode", "ai"])
        self.assertGreater(boosted, base)

    def test_floor_at_01(self):
        rel = instagram._compute_relevance("quantum physics", "cat dancing video")
        self.assertGreaterEqual(rel, 0.1)

    def test_empty_query_returns_default(self):
        rel = instagram._compute_relevance("", "Some video title")
        self.assertEqual(rel, 0.5)


class TestInstagramDepthConfig(unittest.TestCase):
    """Tests for DEPTH_CONFIG."""

    def test_all_depths_exist(self):
        for depth in ("quick", "default", "deep"):
            self.assertIn(depth, instagram.DEPTH_CONFIG)

    def test_required_keys(self):
        for depth, config in instagram.DEPTH_CONFIG.items():
            self.assertIn("results_per_page", config)
            self.assertIn("max_captions", config)

    def test_deep_has_more_results(self):
        self.assertGreater(
            instagram.DEPTH_CONFIG["deep"]["results_per_page"],
            instagram.DEPTH_CONFIG["quick"]["results_per_page"],
        )


if __name__ == "__main__":
    unittest.main()

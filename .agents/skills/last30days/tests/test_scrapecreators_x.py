"""Tests for scrapecreators_x module."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from lib import scrapecreators_x


class TestTokenize(unittest.TestCase):
    def test_lowercases(self):
        tokens = scrapecreators_x._tokenize("Claude AI")
        self.assertIn("claude", tokens)

    def test_strips_stopwords(self):
        tokens = scrapecreators_x._tokenize("the best AI tool")
        self.assertNotIn("the", tokens)
        self.assertIn("best", tokens)  # 'best' is not a stopword in tokenizer

    def test_removes_single_char(self):
        tokens = scrapecreators_x._tokenize("a b cd ef")
        self.assertNotIn("a", tokens)
        self.assertNotIn("b", tokens)
        self.assertIn("cd", tokens)

    def test_expands_synonyms(self):
        tokens = scrapecreators_x._tokenize("ai research")
        self.assertIn("artificial", tokens)
        self.assertIn("intelligence", tokens)


class TestComputeRelevance(unittest.TestCase):
    def test_exact_match_high(self):
        score = scrapecreators_x._compute_relevance("claude code", "claude code is amazing")
        self.assertGreaterEqual(score, 0.8)

    def test_no_match_low(self):
        score = scrapecreators_x._compute_relevance("claude code", "pizza recipes today")
        self.assertLessEqual(score, 0.2)

    def test_empty_query_returns_neutral(self):
        score = scrapecreators_x._compute_relevance("", "some text")
        self.assertEqual(score, 0.5)

    def test_floor_at_01(self):
        score = scrapecreators_x._compute_relevance("abcdef ghijkl", "xyz")
        self.assertGreaterEqual(score, 0.1)


class TestExtractCoreSubject(unittest.TestCase):
    def test_strips_prefix(self):
        result = scrapecreators_x._extract_core_subject("what are people saying about claude")
        self.assertEqual(result, "claude")

    def test_strips_noise(self):
        result = scrapecreators_x._extract_core_subject("latest trending news claude code")
        self.assertNotIn("latest", result)
        self.assertNotIn("trending", result)
        self.assertIn("claude", result)

    def test_preserves_core(self):
        result = scrapecreators_x._extract_core_subject("react native")
        self.assertEqual(result, "react native")


class TestParseDate(unittest.TestCase):
    def test_twitter_format(self):
        item = {"created_at": "Wed Oct 10 20:19:24 +0000 2018"}
        self.assertEqual(scrapecreators_x._parse_date(item), "2018-10-10")

    def test_unix_timestamp(self):
        item = {"timestamp": 1705363200}
        self.assertEqual(scrapecreators_x._parse_date(item), "2024-01-16")

    def test_iso_format(self):
        item = {"created_at": "2024-06-15T12:00:00Z"}
        self.assertEqual(scrapecreators_x._parse_date(item), "2024-06-15")

    def test_none_returns_none(self):
        self.assertIsNone(scrapecreators_x._parse_date({}))


class TestSearchX(unittest.TestCase):
    def test_no_token_returns_error(self):
        result = scrapecreators_x.search_x("test", "2024-01-01", "2024-12-31")
        self.assertEqual(result["items"], [])
        self.assertIn("No SCRAPECREATORS_API_KEY", result["error"])

    def test_parse_x_response(self):
        response = {"items": [{"id": "1", "text": "hello"}]}
        items = scrapecreators_x.parse_x_response(response)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["text"], "hello")

    def test_parse_empty_response(self):
        items = scrapecreators_x.parse_x_response({})
        self.assertEqual(items, [])


class TestDepthConfig(unittest.TestCase):
    def test_all_depths_exist(self):
        for depth in ("quick", "default", "deep"):
            self.assertIn(depth, scrapecreators_x.DEPTH_CONFIG)

    def test_deep_has_more_results(self):
        quick = scrapecreators_x.DEPTH_CONFIG["quick"]["results_per_page"]
        deep = scrapecreators_x.DEPTH_CONFIG["deep"]["results_per_page"]
        self.assertGreater(deep, quick)


if __name__ == "__main__":
    unittest.main()

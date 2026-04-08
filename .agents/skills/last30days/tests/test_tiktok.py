"""Tests for TikTok module (search, normalize, score, dedupe, render)."""

import json
import sys
import unittest
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib import schema, score, normalize, dedupe, render
from lib import tiktok


class TestTikTokRelevance(unittest.TestCase):
    """Test relevance scoring for TikTok items."""

    def test_exact_match(self):
        rel = tiktok._compute_relevance("claude code", "Claude Code tricks and tips")
        self.assertGreaterEqual(rel, 0.8)

    def test_partial_match(self):
        rel = tiktok._compute_relevance("claude code tips", "Best AI tools for coding")
        self.assertLess(rel, 0.5)

    def test_hashtag_boost(self):
        """Hashtags should boost relevance."""
        rel_no_hash = tiktok._compute_relevance("claude code", "random video about stuff")
        rel_with_hash = tiktok._compute_relevance("claude code", "random video about stuff", ["claudecode", "ai"])
        self.assertGreater(rel_with_hash, rel_no_hash)

    def test_empty_query(self):
        rel = tiktok._compute_relevance("", "Some video title")
        self.assertEqual(rel, 0.5)

    def test_floor(self):
        rel = tiktok._compute_relevance("quantum physics", "cat dancing video")
        self.assertGreaterEqual(rel, 0.1)


class TestExtractCoreSubject(unittest.TestCase):
    """Test core subject extraction for TikTok search."""

    def test_strips_prefix(self):
        result = tiktok._extract_core_subject("what are the best claude code tips")
        self.assertNotIn("what are the best", result)
        self.assertIn("claude", result)

    def test_strips_noise(self):
        result = tiktok._extract_core_subject("latest trending updates on React")
        self.assertNotIn("latest", result)
        self.assertNotIn("trending", result)
        self.assertIn("react", result.lower())

    def test_preserves_core(self):
        result = tiktok._extract_core_subject("Claude Code")
        self.assertEqual(result, "claude code")


class TestParseDate(unittest.TestCase):
    """Test date parsing from ScrapeCreators items."""

    def test_unix_timestamp(self):
        item = {"create_time": 1756403075}
        result = tiktok._parse_date(item)
        self.assertIsNotNone(result)
        self.assertRegex(result, r"\d{4}-\d{2}-\d{2}")

    def test_no_date(self):
        item = {}
        self.assertIsNone(tiktok._parse_date(item))


class TestCleanWebVTT(unittest.TestCase):
    """Test WebVTT transcript cleaning."""

    def test_strips_timestamps(self):
        raw = "WEBVTT\n\n00:00:00.000 --> 00:00:02.000\nHello world\n\n00:00:02.000 --> 00:00:04.000\nGoodbye"
        result = tiktok._clean_webvtt(raw)
        self.assertEqual(result, "Hello world Goodbye")

    def test_empty_input(self):
        self.assertEqual(tiktok._clean_webvtt(""), "")
        self.assertEqual(tiktok._clean_webvtt(None), "")


class TestNormalizeTikTokItems(unittest.TestCase):
    """Test TikTok normalization."""

    def setUp(self):
        self.fixtures_dir = Path(__file__).parent.parent / "fixtures"
        with open(self.fixtures_dir / "tiktok_search.json") as f:
            data = json.load(f)
        self.raw_items = data["items"]

    def test_normalizes_items(self):
        items = normalize.normalize_tiktok_items(self.raw_items, "2026-02-01", "2026-03-03")
        self.assertEqual(len(items), 3)
        self.assertIsInstance(items[0], schema.TikTokItem)

    def test_ids_are_sequential(self):
        items = normalize.normalize_tiktok_items(self.raw_items, "2026-02-01", "2026-03-03")
        self.assertEqual(items[0].id, "TK1")
        self.assertEqual(items[1].id, "TK2")
        self.assertEqual(items[2].id, "TK3")

    def test_engagement_parsed(self):
        items = normalize.normalize_tiktok_items(self.raw_items, "2026-02-01", "2026-03-03")
        eng = items[0].engagement
        self.assertIsNotNone(eng)
        self.assertEqual(eng.views, 2100000)
        self.assertEqual(eng.likes, 45000)
        self.assertEqual(eng.shares, 8400)

    def test_hashtags_preserved(self):
        items = normalize.normalize_tiktok_items(self.raw_items, "2026-02-01", "2026-03-03")
        self.assertEqual(items[0].hashtags, ["claudecode", "ai", "coding"])

    def test_caption_snippet_preserved(self):
        items = normalize.normalize_tiktok_items(self.raw_items, "2026-02-01", "2026-03-03")
        self.assertIn("slash commands", items[0].caption_snippet)


class TestScoreTikTokItems(unittest.TestCase):
    """Test TikTok scoring."""

    def test_engagement_scoring(self):
        eng = schema.Engagement(views=1000000, likes=50000, num_comments=2000)
        raw = score.compute_tiktok_engagement_raw(eng)
        self.assertIsNotNone(raw)
        self.assertGreater(raw, 0)

    def test_none_engagement(self):
        raw = score.compute_tiktok_engagement_raw(None)
        self.assertIsNone(raw)

    def test_empty_engagement(self):
        eng = schema.Engagement()
        raw = score.compute_tiktok_engagement_raw(eng)
        self.assertIsNone(raw)

    def test_scoring_pipeline(self):
        items = [
            schema.TikTokItem(
                id="TK1", text="High views video", url="https://tiktok.com/1",
                author_name="creator1", date="2026-03-01",
                engagement=schema.Engagement(views=2000000, likes=50000, num_comments=1000),
                relevance=0.9,
            ),
            schema.TikTokItem(
                id="TK2", text="Low views video", url="https://tiktok.com/2",
                author_name="creator2", date="2026-02-20",
                engagement=schema.Engagement(views=1000, likes=50, num_comments=5),
                relevance=0.5,
            ),
        ]
        scored = score.score_tiktok_items(items)
        self.assertEqual(len(scored), 2)
        self.assertGreater(scored[0].score, 0)
        self.assertGreater(scored[0].score, scored[1].score)


class TestDedupeTikTok(unittest.TestCase):
    """Test TikTok deduplication."""

    def test_no_dupes(self):
        items = [
            schema.TikTokItem(id="TK1", text="Totally different video A",
                              url="https://tiktok.com/1", author_name="a", score=80),
            schema.TikTokItem(id="TK2", text="Completely unique video B",
                              url="https://tiktok.com/2", author_name="b", score=70),
        ]
        result = dedupe.dedupe_tiktok(items)
        self.assertEqual(len(result), 2)

    def test_removes_dupes(self):
        items = [
            schema.TikTokItem(id="TK1", text="Claude Code is amazing for AI coding",
                              url="https://tiktok.com/1", author_name="a", score=80),
            schema.TikTokItem(id="TK2", text="Claude Code is amazing for AI coding wow",
                              url="https://tiktok.com/2", author_name="a", score=60),
        ]
        result = dedupe.dedupe_tiktok(items)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, "TK1")  # Higher score kept


class TestRenderTikTok(unittest.TestCase):
    """Test TikTok rendering in reports."""

    def test_renders_tiktok_section(self):
        report = schema.Report(
            topic="test", range_from="2026-02-01", range_to="2026-03-03",
            generated_at="2026-03-03T00:00:00Z", mode="all",
            tiktok=[
                schema.TikTokItem(
                    id="TK1", text="Video caption here", url="https://tiktok.com/1",
                    author_name="creator", date="2026-03-01", score=85,
                    engagement=schema.Engagement(views=1000000, likes=50000),
                    hashtags=["ai", "coding"],
                    why_relevant="TikTok: Video caption here",
                ),
            ],
        )
        output = render.render_compact(report)
        self.assertIn("### TikTok Videos", output)
        self.assertIn("TK1", output)
        self.assertIn("@creator", output)
        self.assertIn("1,000,000 views", output)

    def test_renders_source_status(self):
        report = schema.Report(
            topic="test", range_from="2026-02-01", range_to="2026-03-03",
            generated_at="2026-03-03T00:00:00Z", mode="all",
            tiktok=[
                schema.TikTokItem(
                    id="TK1", text="test", url="https://tiktok.com/1",
                    author_name="creator", caption_snippet="some caption",
                ),
            ],
        )
        status = render.render_source_status(report)
        self.assertIn("TikTok", status)
        self.assertIn("1 videos", status)

    def test_xref_tag_tiktok(self):
        """Test that TK prefix is recognized in cross-ref tags."""
        item = schema.RedditItem(id="R1", title="test", url="test", subreddit="test",
                                  cross_refs=["TK1"])
        tag = render._xref_tag(item)
        self.assertIn("TikTok", tag)


class TestSchemaRoundtrip(unittest.TestCase):
    """Test TikTokItem serialization round-trip via Report."""

    def test_to_dict_and_back(self):
        original = schema.TikTokItem(
            id="TK1", text="Test caption", url="https://tiktok.com/1",
            author_name="creator", date="2026-03-01",
            date_confidence="high",
            engagement=schema.Engagement(views=100, likes=10, num_comments=5, shares=3),
            caption_snippet="spoken words",
            hashtags=["test", "ai"],
            relevance=0.8, why_relevant="TikTok: Test",
            subs=schema.SubScores(relevance=80, recency=90, engagement=70),
            score=80, cross_refs=["R1"],
        )
        report = schema.Report(
            topic="test", range_from="2026-02-01", range_to="2026-03-03",
            generated_at="2026-03-03T00:00:00Z", mode="all",
            tiktok=[original],
        )
        d = report.to_dict()
        restored = schema.Report.from_dict(d)
        self.assertEqual(len(restored.tiktok), 1)
        tk = restored.tiktok[0]
        self.assertEqual(tk.id, "TK1")
        self.assertEqual(tk.author_name, "creator")
        self.assertEqual(tk.hashtags, ["test", "ai"])
        self.assertEqual(tk.engagement.views, 100)
        self.assertEqual(tk.engagement.shares, 3)
        self.assertEqual(tk.caption_snippet, "spoken words")
        self.assertEqual(tk.cross_refs, ["R1"])


if __name__ == "__main__":
    unittest.main()

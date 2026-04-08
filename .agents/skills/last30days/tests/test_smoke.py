"""End-to-end smoke tests — run the actual script as subprocess."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT = str(Path(__file__).parent.parent / "scripts" / "last30days.py")


def _run(args, timeout=30):
    """Run last30days.py with args, return (returncode, stdout, stderr)."""
    result = subprocess.run(
        [sys.executable, SCRIPT] + args,
        capture_output=True, text=True, timeout=timeout,
    )
    return result.returncode, result.stdout, result.stderr


class TestDiagnose(unittest.TestCase):
    """Tests for --diagnose flag."""

    def test_exits_zero(self):
        rc, stdout, stderr = _run(["--diagnose"])
        self.assertEqual(rc, 0, f"--diagnose failed: {stderr}")

    def test_returns_valid_json(self):
        rc, stdout, stderr = _run(["--diagnose"])
        data = json.loads(stdout)
        self.assertIsInstance(data, dict)

    def test_has_expected_keys(self):
        rc, stdout, stderr = _run(["--diagnose"])
        data = json.loads(stdout)
        for key in ("openai", "xai", "youtube", "tiktok", "instagram", "hackernews", "polymarket"):
            self.assertIn(key, data, f"Missing key: {key}")

    def test_boolean_values(self):
        rc, stdout, stderr = _run(["--diagnose"])
        data = json.loads(stdout)
        for key in ("openai", "xai", "youtube", "tiktok", "instagram", "hackernews", "polymarket"):
            self.assertIsInstance(data[key], bool, f"{key} should be boolean")

    def test_hackernews_always_true(self):
        data = json.loads(_run(["--diagnose"])[1])
        self.assertTrue(data["hackernews"])

    def test_polymarket_always_true(self):
        data = json.loads(_run(["--diagnose"])[1])
        self.assertTrue(data["polymarket"])


class TestHelp(unittest.TestCase):
    """Tests for --help flag."""

    def test_exits_zero(self):
        rc, stdout, stderr = _run(["--help"])
        self.assertEqual(rc, 0)

    def test_shows_usage(self):
        rc, stdout, stderr = _run(["--help"])
        self.assertTrue(
            "topic" in stdout.lower() or "usage" in stdout.lower(),
            "Expected usage info in help output"
        )


class TestNoTopic(unittest.TestCase):
    """Tests for missing topic."""

    def test_exits_nonzero_without_topic(self):
        rc, stdout, stderr = _run([])
        self.assertNotEqual(rc, 0)

    def test_error_message(self):
        rc, stdout, stderr = _run([])
        self.assertTrue(
            "topic" in stderr.lower() or "error" in stderr.lower(),
            "Expected error about missing topic"
        )


class TestMockMode(unittest.TestCase):
    """Tests for --mock mode (fixture-based, no API calls)."""

    def test_mock_json_exits_zero(self):
        rc, stdout, stderr = _run(["--mock", "--emit", "json", "test topic"], timeout=120)
        self.assertEqual(rc, 0, f"--mock failed: {stderr}")

    def test_mock_json_valid(self):
        rc, stdout, stderr = _run(["--mock", "--emit", "json", "test topic"], timeout=120)
        data = json.loads(stdout)
        self.assertIn("topic", data)
        self.assertEqual(data["topic"], "test topic")


if __name__ == "__main__":
    unittest.main()

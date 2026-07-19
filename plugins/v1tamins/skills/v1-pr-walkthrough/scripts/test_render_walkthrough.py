#!/usr/bin/env python3
"""Focused tests for the PR walkthrough renderer."""

from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
SPEC = importlib.util.spec_from_file_location(
    "render_walkthrough", SCRIPT_DIR / "render_walkthrough.py"
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("could not load render_walkthrough.py")
RENDERER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RENDERER)


class RenderWalkthroughTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = json.loads(
            (SKILL_DIR / "references" / "walkthrough-data.example.json").read_text(
                encoding="utf-8"
            )
        )
        cls.template = RENDERER.load_template()

    def test_example_renders_static_accessible_content(self) -> None:
        output = RENDERER.render(self.data, self.template)

        self.assertNotRegex(output, r"@@[A-Z0-9_]+@@")
        self.assertIn('href="#main-content"', output)
        self.assertIn('role="region" aria-label="Touched files table"', output)
        self.assertIn('aria-sort="none"', output)
        self.assertIn('role="status" aria-live="polite"', output)
        self.assertIn('id="file-report-route"', output)
        self.assertIn('data-layer-label="API Boundary"', output)
        self.assertIn('href="#file-report-route"', output)
        self.assertIn('id="layer-api"', output)
        self.assertIn("ReportDeliveryService.enqueue", output)
        self.assertIn("<svg", output)
        self.assertIn("marker-end=", output)
        self.assertEqual(output.count('data-file-id="'), len(self.data["files"]))

    def test_unknown_layer_is_rejected(self) -> None:
        data = copy.deepcopy(self.data)
        data["files"][0]["layer_id"] = "missing"

        with self.assertRaisesRegex(ValueError, "does not match a layer"):
            RENDERER.render(data, self.template)

    def test_layer_without_snippet_or_reason_is_rejected(self) -> None:
        data = copy.deepcopy(self.data)
        data["layers"][0]["snippets"] = []

        with self.assertRaisesRegex(ValueError, "needs snippets or no_snippet_reason"):
            RENDERER.render(data, self.template)

    def test_flowchart_edge_requires_evidence(self) -> None:
        data = copy.deepcopy(self.data)
        del data["flowchart"]["edges"][0]["evidence"]

        with self.assertRaisesRegex(ValueError, "evidence is required"):
            RENDERER.render(data, self.template)


if __name__ == "__main__":
    unittest.main()

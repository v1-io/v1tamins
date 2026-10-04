#!/usr/bin/env python3
"""Offline regression checks for document and video conversion boundaries."""

import importlib.util
from pathlib import Path
from subprocess import CompletedProcess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


DOC = load("md2docs", "plugins/v1tamins/skills/v1-md2docs/scripts/md2docs.py")
VIDEO = load("video_to_gif", "plugins/v1tamins/skills/v1-prove-work/scripts/video_to_gif.py")


class DiagramTests(unittest.TestCase):
    def render(self, source, renderer):
        with patch("shutil.which", side_effect=lambda name: "mmdc" if name == "mmdc" else None):
            with patch.object(DOC.subprocess, "run", side_effect=renderer):
                return DOC.render_mermaid_blocks(source)

    def test_failed_diagram_does_not_hide_later_success(self):
        paths = []

        def renderer(argv, **kwargs):
            source = Path(argv[argv.index("-i") + 1])
            output = Path(argv[argv.index("-o") + 1])
            paths.append(source.parent)
            failed = "invalid" in source.read_text()
            # Failure may leave partial output, which must not be accepted.
            output.write_bytes(b"partial" if failed else b"valid-image")
            return CompletedProcess(argv, 1 if failed else 0)

        text, images = self.render("```mermaid\ninvalid\n```\n```mermaid\ngraph TD; A-->B\n```", renderer)
        result = DOC.inject_mermaid_images(text, images)
        self.assertEqual(len(images), 1)
        self.assertIn("invalid", result)
        self.assertIn("<img ", result)
        self.assertNotIn("MERMAID_IMAGE_", result)
        self.assertEqual(len(set(paths)), 2)
        self.assertTrue(all(not path.exists() for path in paths))

    def test_failed_render_does_not_reuse_shared_temp_output(self):
        with tempfile.TemporaryDirectory() as directory:
            stale = Path(directory) / "md2docs_mermaid_0.png"
            stale.write_bytes(b"another-document")
            with patch.object(DOC.tempfile, "gettempdir", return_value=directory):
                text, images = self.render("```mermaid\ninvalid\n```", lambda argv, **kw: CompletedProcess(argv, 1))
            self.assertEqual(images, [])
            self.assertIn("invalid", text)
            self.assertEqual(stale.read_bytes(), b"another-document")

    def test_timeout_cleans_up_source(self):
        paths = []

        def renderer(argv, **kwargs):
            paths.append(Path(argv[argv.index("-i") + 1]).parent)
            raise DOC.subprocess.TimeoutExpired(argv, 30)

        _, images = self.render("```mermaid\ngraph TD; A-->B\n```", renderer)
        self.assertEqual(images, [])
        self.assertTrue(all(not path.exists() for path in paths))

    def test_double_digit_placeholders_do_not_match_prefixes(self):
        images = [f'<img alt="{i}">' for i in range(12)]
        rendered = DOC.inject_mermaid_images("<p>MERMAID_IMAGE_10</p>\nMERMAID_IMAGE_1", images)
        self.assertEqual(rendered, '<img alt="10">\n<img alt="1">')


class VideoTests(unittest.TestCase):
    def test_requested_settings_reach_conversion(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "demo.gif"

            def save(frames, path, **kwargs):
                path.write_bytes(b"gif")

            with patch.object(VIDEO, "check_gifsicle", return_value=False), \
                 patch.object(VIDEO, "decode_webm", return_value=[object()]) as decode, \
                 patch.object(VIDEO, "save_gif", side_effect=save) as encode:
                VIDEO.enforce_size_limit(Path("input.webm"), output, 1024, fps=5, max_width=320, colors=32)
            decode.assert_called_once_with(Path("input.webm"), target_fps=5, max_width=320)
            self.assertEqual(encode.call_args.kwargs, {"fps": 5, "colors": 32})
            self.assertEqual(output.read_bytes(), b"gif")

    def test_reductions_never_increase_requested_quality(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "demo.gif"

            def save(frames, path, **kwargs):
                path.write_bytes(b"too large")

            with patch.object(VIDEO, "check_gifsicle", return_value=False), \
                 patch.object(VIDEO, "decode_webm", return_value=[object()] * 100) as decode, \
                 patch.object(VIDEO, "save_gif", side_effect=save) as encode:
                with self.assertRaises(SystemExit):
                    VIDEO.enforce_size_limit(Path("input.webm"), output, 1, fps=5, max_width=320, colors=32)
            self.assertEqual(decode.call_count, 2)
            self.assertTrue(all(c.kwargs == {"target_fps": 5, "max_width": 320} for c in decode.call_args_list))
            self.assertEqual(len(encode.call_args.args[0]), 50)

    def test_cli_passes_settings_and_rejects_invalid_input_before_dependencies(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.webm"
            source.write_bytes(b"fixture")
            argv = ["video_to_gif.py", "--input", str(source), "--output", str(Path(directory) / "out.gif"),
                    "--fps", "5", "--max-width", "320", "--colors", "32"]
            with patch.object(VIDEO.sys, "argv", argv), patch.object(VIDEO, "ensure_dependencies"), \
                 patch.object(VIDEO, "check_gifsicle", return_value=True), \
                 patch.object(VIDEO, "OUTPUT_DIR", Path(directory)), \
                 patch.object(VIDEO, "enforce_size_limit") as convert:
                VIDEO.main()
            self.assertEqual(convert.call_args.args[3:], (5, 320, 32))
            with patch.object(VIDEO.sys, "argv", argv + ["--fps", "0"]), \
                 patch.object(VIDEO, "ensure_dependencies") as dependencies:
                with self.assertRaises(SystemExit) as caught:
                    VIDEO.main()
            self.assertEqual(caught.exception.code, 2)
            dependencies.assert_not_called()


if __name__ == "__main__":
    unittest.main()

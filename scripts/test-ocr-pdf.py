#!/usr/bin/env python3
"""Exercise the macOS Vision OCR helper and its page-failure contract."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "plugins/v1tamins/skills/v1-canon2skill/scripts/ocr-pdf-macos.swift"


def synthetic_pdf(page_count: int = 2) -> bytes:
    """Build a small vector-text PDF without a third-party PDF dependency."""

    objects: dict[int, bytes] = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
    }
    page_numbers = list(range(3, 3 + page_count))
    content_numbers = list(range(3 + page_count + 1, 3 + (page_count * 2) + 1))
    kids = " ".join(f"{number} 0 R" for number in page_numbers)
    objects[2] = (
        f"<< /Type /Pages /Kids [{kids}] /Count {page_count} >>".encode()
    )

    for index, (page_number, content_number) in enumerate(
        zip(page_numbers, content_numbers), start=1
    ):
        objects[page_number] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 {3 + page_count} 0 R >> >> "
            f"/Contents {content_number} 0 R >>"
        ).encode()
        text = f"OCR smoke test page {index}".encode()
        content = b"BT\n/F1 24 Tf\n72 700 Td\n(" + text + b") Tj\nET\n"
        objects[content_number] = (
            f"<< /Length {len(content)} >>\nstream\n".encode()
            + content
            + b"endstream"
        )

    objects[3 + page_count] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"

    document = bytearray(b"%PDF-1.4\n")
    offsets: dict[int, int] = {}
    for number in sorted(objects):
        offsets[number] = len(document)
        document.extend(f"{number} 0 obj\n".encode())
        document.extend(objects[number])
        document.extend(b"\nendobj\n")

    xref_offset = len(document)
    size = max(objects) + 1
    document.extend(f"xref\n0 {size}\n".encode())
    document.extend(b"0000000000 65535 f \n")
    for number in range(1, size):
        document.extend(f"{offsets[number]:010d} 00000 n \n".encode())
    document.extend(
        f"trailer\n<< /Size {size} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n".encode()
    )
    return bytes(document)


def clean_swift_environment(module_cache: Path) -> dict[str, str]:
    """Keep helper tests isolated from ambient credentials and caches."""

    return {
        "PATH": os.defpath,
        "SWIFT_MODULECACHE_PATH": str(module_cache),
        "TMPDIR": str(module_cache.parent),
    }


def normalized(text: str) -> str:
    """Compare OCR text without depending on line wrapping or case."""

    return " ".join(text.split()).casefold()


def compile_helper(source: Path, destination: Path, root: Path) -> subprocess.CompletedProcess[str]:
    module_cache = root / f"module-cache-{destination.stem}"
    module_cache.mkdir()
    return subprocess.run(
        [
            "/usr/bin/swiftc",
            "-module-cache-path",
            str(module_cache),
            str(source),
            "-o",
            str(destination),
        ],
        env=clean_swift_environment(module_cache),
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def failure_variant(source: str, *, all_pages: bool) -> str:
    """Inject only a render or recognition boundary into a temporary copy."""

    if all_pages:
        call = "let lines = try recognize(image)"
        replacement = "let lines = try recognizeForTest(image)"
        body = """func recognizeForTest(_ image: CGImage) throws -> [String] {
    throw OCRPageError.visionFailed("synthetic Vision boundary failure")
}
"""
        marker = "var output = \"\""
    else:
        call = "let image = try render(page)"
        replacement = "let image = try renderForTest(page, pageNumber: pageNumber)"
        body = """func renderForTest(_ page: CGPDFPage, pageNumber: Int) throws -> CGImage {
    if pageNumber == 2 {
        throw OCRPageError.renderFailed
    }
    return try render(page)
}
"""
        marker = "func recognize(_ image: CGImage) throws -> [String] {"
    if source.count(call) != 1:
        raise AssertionError("OCR helper failure boundary changed unexpectedly")
    if source.count(marker) != 1:
        raise AssertionError("OCR helper insertion boundary changed unexpectedly")
    return source.replace(call, replacement, 1).replace(marker, body + marker, 1)


@unittest.skipUnless(sys.platform == "darwin", "Vision OCR helper requires macOS")
class OCRHelperTests(unittest.TestCase):
    def test_success_partial_failure_and_all_failure_outcomes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="v1tamins-ocr-") as directory:
            root = Path(directory)
            source_pdf = root / "source.pdf"
            source_pdf.write_bytes(synthetic_pdf())

            helper = root / "ocr-pdf"
            compiled = compile_helper(HELPER, helper, root)
            self.assertEqual(compiled.returncode, 0, compiled.stderr)

            successful_output = root / "successful.txt"
            success_runtime_cache = root / "success-runtime-cache"
            success_runtime_cache.mkdir()
            successful = subprocess.run(
                [str(helper), str(source_pdf), str(successful_output)],
                env=clean_swift_environment(success_runtime_cache),
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            self.assertEqual(successful.returncode, 0, successful.stderr)
            successful_text = successful_output.read_text()
            self.assertIn("=== Page 1 ===", successful_text)
            self.assertIn("=== Page 2 ===", successful_text)
            self.assertNotIn("=== OCR Failure Summary ===", successful_text)
            successful_normalized = normalized(successful_text)
            self.assertIn("ocr smoke test page 1", successful_normalized)
            self.assertIn("ocr smoke test page 2", successful_normalized)

            partial_source = root / "ocr-partial.swift"
            partial_source.write_text(
                failure_variant(HELPER.read_text(), all_pages=False)
            )
            partial_helper = root / "ocr-partial"
            partial_compiled = compile_helper(partial_source, partial_helper, root)
            self.assertEqual(partial_compiled.returncode, 0, partial_compiled.stderr)

            partial_output = root / "partial.txt"
            partial_runtime_cache = root / "partial-runtime-cache"
            partial_runtime_cache.mkdir()
            partial = subprocess.run(
                [str(partial_helper), str(source_pdf), str(partial_output)],
                env=clean_swift_environment(partial_runtime_cache),
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            self.assertEqual(partial.returncode, 2, partial.stderr)
            partial_text = partial_output.read_text()
            self.assertIn("=== Page 1 ===", partial_text)
            self.assertIn("=== Page 2 ===", partial_text)
            self.assertIn("[OCR render failed:", partial_text)
            self.assertIn("=== OCR Failure Summary ===", partial_text)
            self.assertIn("failed_pages=1 total_pages=2 successful_pages=1", partial_text)
            self.assertIn("ocr smoke test page 1", normalized(partial_text))

            all_source = root / "ocr-all-failed.swift"
            all_source.write_text(
                failure_variant(HELPER.read_text(), all_pages=True)
            )
            all_helper = root / "ocr-all-failed"
            all_compiled = compile_helper(all_source, all_helper, root)
            self.assertEqual(all_compiled.returncode, 0, all_compiled.stderr)

            all_output = root / "all-failed.txt"
            all_runtime_cache = root / "all-runtime-cache"
            all_runtime_cache.mkdir()
            all_failed = subprocess.run(
                [str(all_helper), str(source_pdf), str(all_output)],
                env=clean_swift_environment(all_runtime_cache),
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            self.assertEqual(all_failed.returncode, 2, all_failed.stderr)
            all_text = all_output.read_text()
            self.assertIn("[OCR vision failed: synthetic Vision boundary failure]", all_text)
            self.assertIn("failed_pages=2 total_pages=2 successful_pages=0", all_text)
            self.assertIn("OCR all pages failed", all_failed.stderr)

            missing_runtime_cache = root / "missing-runtime-cache"
            missing_runtime_cache.mkdir()
            missing = subprocess.run(
                [str(helper), str(root / "missing.pdf"), str(root / "missing.txt")],
                env=clean_swift_environment(missing_runtime_cache),
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            self.assertNotEqual(missing.returncode, 0)
            self.assertFalse((root / "missing.txt").exists())


if __name__ == "__main__":
    unittest.main()

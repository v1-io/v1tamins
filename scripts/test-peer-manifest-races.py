#!/usr/bin/env python3
"""Offline regressions for descriptor-relative peer manifest observation."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT_DIR = Path(__file__).resolve().parent
PEER_SCRIPTS = SCRIPT_DIR.parent / "plugins/v1tamins/skills/v1-phone-a-friend/scripts"
sys.path.insert(0, str(PEER_SCRIPTS))

import peer_boundary  # noqa: E402


class ManifestRaceTests(unittest.TestCase):
    def test_internal_symlink_is_recorded_without_reading_destination(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "data.txt").write_text("inside\n")
            (root / "alias.txt").symlink_to("data.txt")
            result = peer_boundary.scan_manifest(root)
            self.assertFalse(result.errors, result)
            self.assertTrue(result.entries["alias.txt"].endswith(":data.txt"))

    def test_normal_nested_manifest_remains_complete(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "root"
            nested = root / "nested"
            nested.mkdir(parents=True)
            (nested / "data.txt").write_text("inside\n", encoding="utf-8")

            result = peer_boundary.scan_manifest(root)

            self.assertFalse(result.errors, result)
            self.assertFalse(result.truncated, result)
            self.assertIn("nested/data.txt", result.entries)

    def test_nested_directory_swap_before_open_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            root = base / "root"
            nested = root / "nested"
            outside = base / "outside"
            nested.mkdir(parents=True)
            outside.mkdir()
            (nested / "inside.txt").write_text("inside\n", encoding="utf-8")
            (outside / "outside.txt").write_text("outside-secret\n", encoding="utf-8")
            replacement = root / "nested-real"
            swapped = False
            original_open = peer_boundary.os.open

            def racing_open(path, flags, mode=0o777, *, dir_fd=None):
                nonlocal swapped
                if (
                    not swapped
                    and path == "nested"
                    and dir_fd is not None
                    and flags & os.O_DIRECTORY
                ):
                    nested.rename(replacement)
                    nested.symlink_to(outside, target_is_directory=True)
                    swapped = True
                return original_open(path, flags, mode, dir_fd=dir_fd)

            with patch.object(peer_boundary.os, "open", racing_open):
                result = peer_boundary.scan_manifest(root)

            self.assertTrue(swapped)
            self.assertTrue(result.errors, result)
            self.assertNotIn("outside.txt", result.entries)
            self.assertNotIn("outside-secret", "\n".join(result.entries.values()))

    def test_ancestor_swap_after_child_descriptor_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            root = base / "root"
            nested = root / "nested"
            outside = base / "outside"
            nested.mkdir(parents=True)
            outside.mkdir()
            (nested / "inside.txt").write_text("inside\n", encoding="utf-8")
            (outside / "outside.txt").write_text("outside-secret\n", encoding="utf-8")
            replacement = root / "nested-real"
            nested_inode = nested.stat().st_ino
            swapped = False
            original_scandir = peer_boundary.os.scandir

            def racing_scandir(path):
                nonlocal swapped
                if not swapped and isinstance(path, int):
                    try:
                        is_nested = os.fstat(path).st_ino == nested_inode
                    except OSError:
                        is_nested = False
                    if is_nested:
                        nested.rename(replacement)
                        nested.symlink_to(outside, target_is_directory=True)
                        swapped = True
                return original_scandir(path)

            with patch.object(peer_boundary.os, "scandir", racing_scandir):
                result = peer_boundary.scan_manifest(root)

            self.assertTrue(swapped)
            self.assertTrue(result.errors, result)
            self.assertNotIn("outside.txt", result.entries)
            self.assertIn("nested/inside.txt", result.entries)

    def test_file_swap_before_content_open_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            root = base / "root"
            outside = base / "outside"
            root.mkdir()
            outside.mkdir()
            victim = root / "victim.txt"
            victim.write_text("inside\n", encoding="utf-8")
            secret = outside / "secret.txt"
            secret.write_text("outside-secret\n", encoding="utf-8")
            replacement = root / "victim-real.txt"
            swapped = False
            original_open = peer_boundary.os.open

            def racing_open(path, flags, mode=0o777, *, dir_fd=None):
                nonlocal swapped
                if (
                    not swapped
                    and path == "victim.txt"
                    and dir_fd is not None
                    and not flags & os.O_DIRECTORY
                ):
                    victim.rename(replacement)
                    victim.symlink_to(secret)
                    swapped = True
                return original_open(path, flags, mode, dir_fd=dir_fd)

            with patch.object(peer_boundary.os, "open", racing_open):
                result = peer_boundary.scan_manifest(root)

            self.assertTrue(swapped)
            self.assertTrue(result.errors, result)
            self.assertNotIn("outside-secret", "\n".join(result.entries.values()))

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO race requires POSIX")
    def test_file_swap_to_fifo_does_not_block(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "root"
            root.mkdir()
            victim = root / "victim.txt"
            victim.write_text("inside\n", encoding="utf-8")
            replacement = root / "victim-real.txt"
            swapped = False
            original_open = peer_boundary.os.open

            def racing_open(path, flags, mode=0o777, *, dir_fd=None):
                nonlocal swapped
                if (
                    not swapped
                    and path == "victim.txt"
                    and dir_fd is not None
                    and not flags & os.O_DIRECTORY
                ):
                    victim.rename(replacement)
                    os.mkfifo(victim)
                    swapped = True
                return original_open(path, flags, mode, dir_fd=dir_fd)

            with patch.object(peer_boundary.os, "open", racing_open):
                result = peer_boundary.scan_manifest(root)

            self.assertTrue(swapped)
            self.assertTrue(result.errors, result)


if __name__ == "__main__":
    unittest.main(verbosity=2)

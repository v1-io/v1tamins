"""Tests for per-project .env config discovery and precedence."""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib import env


class TestFindProjectEnv(unittest.TestCase):
    """Tests for _find_project_env() directory walking."""

    def test_finds_env_in_cwd(self, ):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            claude_dir = Path(tmpdir) / ".claude"
            claude_dir.mkdir()
            env_file = claude_dir / "last30days.env"
            env_file.write_text("OPENAI_API_KEY=sk-test\n")
            with patch.object(Path, 'cwd', return_value=Path(tmpdir)):
                result = env._find_project_env()
                self.assertIsNotNone(result)
                self.assertEqual(result.name, "last30days.env")

    def test_returns_none_when_no_config(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(Path, 'cwd', return_value=Path(tmpdir)):
                result = env._find_project_env()
                self.assertIsNone(result)


class TestConfigPrecedence(unittest.TestCase):
    """Tests for config source priority."""

    def test_project_overrides_global(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create global config
            global_dir = Path(tmpdir) / "global"
            global_dir.mkdir()
            global_env = global_dir / ".env"
            global_env.write_text("BRAVE_API_KEY=global-key\nPARALLEL_API_KEY=global-only\n")

            # Create project config
            project_dir = Path(tmpdir) / "project" / ".claude"
            project_dir.mkdir(parents=True)
            project_env = project_dir / "last30days.env"
            project_env.write_text("BRAVE_API_KEY=project-key\n")

            with patch.object(Path, 'cwd', return_value=Path(tmpdir) / "project"), \
                 patch.object(env, 'CONFIG_FILE', global_env), \
                 patch.dict(os.environ, {}, clear=False):
                # Remove any env vars that would override
                for k in ('BRAVE_API_KEY', 'PARALLEL_API_KEY', 'OPENAI_API_KEY'):
                    os.environ.pop(k, None)
                config = env.get_config()
                # Project value wins over global
                self.assertEqual(config['BRAVE_API_KEY'], 'project-key')
                # Global value still available for keys not in project
                self.assertEqual(config['PARALLEL_API_KEY'], 'global-only')

    def test_env_var_overrides_project(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / ".claude"
            project_dir.mkdir()
            project_env = project_dir / "last30days.env"
            project_env.write_text("BRAVE_API_KEY=project-key\n")

            with patch.object(Path, 'cwd', return_value=Path(tmpdir)), \
                 patch.object(env, 'CONFIG_FILE', None), \
                 patch.dict(os.environ, {'BRAVE_API_KEY': 'env-key'}):
                config = env.get_config()
                self.assertEqual(config['BRAVE_API_KEY'], 'env-key')


class TestConfigSource(unittest.TestCase):
    """Tests for _CONFIG_SOURCE tracking."""

    def test_tracks_project_source(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / ".claude"
            project_dir.mkdir()
            project_env = project_dir / "last30days.env"
            project_env.write_text("BRAVE_API_KEY=test\n")

            with patch.object(Path, 'cwd', return_value=Path(tmpdir)), \
                 patch.object(env, 'CONFIG_FILE', None):
                config = env.get_config()
                self.assertIn('project:', config['_CONFIG_SOURCE'])

    def test_tracks_global_source(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            global_env = Path(tmpdir) / ".env"
            global_env.write_text("BRAVE_API_KEY=test\n")

            with patch.object(Path, 'cwd', return_value=Path(tmpdir)), \
                 patch.object(env, 'CONFIG_FILE', global_env):
                config = env.get_config()
                self.assertIn('global:', config['_CONFIG_SOURCE'])

    def test_tracks_env_only(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(Path, 'cwd', return_value=Path(tmpdir)), \
                 patch.object(env, 'CONFIG_FILE', None):
                config = env.get_config()
                self.assertEqual(config['_CONFIG_SOURCE'], 'env_only')


class TestConfigExists(unittest.TestCase):
    """Tests for config_exists() with project support."""

    def test_true_with_project_env(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / ".claude"
            project_dir.mkdir()
            (project_dir / "last30days.env").write_text("KEY=val\n")
            with patch.object(Path, 'cwd', return_value=Path(tmpdir)):
                self.assertTrue(env.config_exists())

    def test_true_with_global_env(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            global_env = Path(tmpdir) / ".env"
            global_env.write_text("KEY=val\n")
            with patch.object(Path, 'cwd', return_value=Path(tmpdir)), \
                 patch.object(env, 'CONFIG_FILE', global_env):
                self.assertTrue(env.config_exists())

    def test_false_with_nothing(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(Path, 'cwd', return_value=Path(tmpdir)), \
                 patch.object(env, 'CONFIG_FILE', None):
                self.assertFalse(env.config_exists())


class TestFilePermissions(unittest.TestCase):
    """Tests for _check_file_permissions() warnings."""

    def test_warns_on_world_readable(self):
        import tempfile
        import io
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / ".env"
            f.write_text("KEY=val\n")
            f.chmod(0o644)
            stderr = io.StringIO()
            with patch('sys.stderr', stderr):
                env._check_file_permissions(f)
            self.assertIn("WARNING", stderr.getvalue())

    def test_no_warning_on_600(self):
        import tempfile
        import io
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / ".env"
            f.write_text("KEY=val\n")
            f.chmod(0o600)
            stderr = io.StringIO()
            with patch('sys.stderr', stderr):
                env._check_file_permissions(f)
            self.assertEqual(stderr.getvalue(), "")


if __name__ == "__main__":
    unittest.main()

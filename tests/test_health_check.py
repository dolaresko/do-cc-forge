import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from conftest import load_hook_module

health_check = load_hook_module("docc-health-check")


class TestStalePaths(unittest.TestCase):
    def test_existing_path_not_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "foo.ts").write_text("", encoding="utf-8")

            content = "See src/foo.ts for details."
            stale = health_check._stale_paths(content, root)

            self.assertEqual(stale, [])

    def test_missing_path_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            content = "See src/gone.ts for details."
            stale = health_check._stale_paths(content, root)

            self.assertEqual(stale, ["src/gone.ts"])

    def test_line_number_suffix_stripped_before_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "lib").mkdir()
            (root / "lib" / "bar.py").write_text("", encoding="utf-8")

            content = "See lib/bar.py:42 for details."
            stale = health_check._stale_paths(content, root)

            self.assertEqual(stale, [])


class TestBackupPreservation(unittest.TestCase):
    """
    compress_markdown() shortens line *content* but never drops lines, so
    the real algorithm rarely trips the `compressed_lc < lc - 5` gate in a
    short test fixture. Stub it out to force the write path deterministically
    and isolate the behavior under test: does a second compress run clobber
    the backup?
    """

    def _run_compress(self, cwd: Path, fake_compressed: str):
        import io
        import json as _json
        import os as _os

        stdin_payload = _json.dumps({"cwd": str(cwd)})
        old_stdin = sys.stdin
        old_env = dict(_os.environ)
        old_compress = health_check.compress_markdown
        old_compress_lines = health_check.COMPRESS_LINES
        try:
            sys.stdin = io.StringIO(stdin_payload)
            _os.environ["DOCC_AUTO_COMPRESS"] = "1"
            # COMPRESS_LINES is read from the env once at module import time,
            # so patch the module attribute directly rather than the env var.
            health_check.COMPRESS_LINES = 1
            health_check.compress_markdown = lambda content: fake_compressed
            with self.assertRaises(SystemExit):
                health_check.main()
        finally:
            sys.stdin = old_stdin
            _os.environ.clear()
            _os.environ.update(old_env)
            health_check.compress_markdown = old_compress
            health_check.COMPRESS_LINES = old_compress_lines

    def test_second_compress_does_not_overwrite_original_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            claudemd = cwd / "CLAUDE.md"
            backup = cwd / "CLAUDE.md.original.md"

            true_original = "# Title\n\n" + "\n".join(f"line {i}" for i in range(30))
            claudemd.write_text(true_original, encoding="utf-8")

            first_pass_compressed = "# Title\n\ncompressed once"
            self._run_compress(cwd, first_pass_compressed)
            self.assertTrue(backup.exists())
            self.assertEqual(backup.read_text(encoding="utf-8"), true_original)
            self.assertEqual(claudemd.read_text(encoding="utf-8"), first_pass_compressed)

            # A second compression pass runs against the already-compressed
            # file. The backup must still hold the ORIGINAL content, not the
            # already-compressed content from the first pass.
            second_pass_compressed = "# Title\n\ncompressed twice"
            self._run_compress(cwd, second_pass_compressed)
            self.assertEqual(backup.read_text(encoding="utf-8"), true_original)


if __name__ == "__main__":
    unittest.main()

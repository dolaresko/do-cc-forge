import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from conftest import load_hook_module

context_monitor = load_hook_module("docc-context-monitor")


class TestUsage(unittest.TestCase):
    def test_no_transcript_path_returns_zero(self):
        self.assertEqual(context_monitor._usage({}), 0.0)

    def test_missing_file_returns_zero(self):
        data = {"transcript_path": "/nonexistent/path/transcript.jsonl"}
        self.assertEqual(context_monitor._usage(data), 0.0)

    def test_reads_transcript_file_size(self, tmp_path=None):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            transcript = Path(tmp) / "transcript.jsonl"
            # CONTEXT_LIMIT chars, at 4 chars/token, is 800_000 bytes for
            # 100% usage. Write a known size and check the ratio.
            content = "x" * 400_000  # half of CONTEXT_LIMIT in tokens
            transcript.write_text(content, encoding="utf-8")

            pct = context_monitor._usage({"transcript_path": str(transcript)})

            expected = (400_000 // 4) / context_monitor.CONTEXT_LIMIT
            self.assertAlmostEqual(pct, expected)
            self.assertGreater(pct, 0)


if __name__ == "__main__":
    unittest.main()

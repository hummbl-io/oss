import io
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from hummbl_eval.cli import main


class CliTests(unittest.TestCase):
    def test_canonicalize_success_and_missing_file(self) -> None:
        class CapturedStdout:
            def __init__(self) -> None:
                self.buffer = io.BytesIO()

        with TemporaryDirectory() as directory:
            path = Path(directory) / "value.json"
            path.write_text('{"b":2,"a":1}', encoding="utf-8")
            output = CapturedStdout()
            with patch("sys.stdout", output):
                self.assertEqual(main(["canonicalize", str(path)]), 0)
            self.assertEqual(output.buffer.getvalue(), b'{"a":1,"b":2}\n')

            with patch("sys.stderr", io.StringIO()):
                self.assertEqual(main(["canonicalize", str(path.with_name("missing"))]), 2)

    def test_gatebench_rejection_has_stable_exit_and_json(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "case.json"
            path.write_text(
                '{"case_id":"GB-P0-X","severity":"P0","claim":"x",'
                '"evidence_refs":[],"receipt_refs":["r"],'
                '"author_id":"a","evaluator_id":"b",'
                '"expected_disposition":"reject"}',
                encoding="utf-8",
            )
            output = io.StringIO()
            with patch("sys.stdout", output):
                code = main(["gatebench", str(path)])
            self.assertEqual(code, 4)
            self.assertIn('"disposition":"reject"', output.getvalue())

    def test_invalid_json_returns_input_error(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text('{"a":1,"a":2}', encoding="utf-8")
            with patch("sys.stderr", io.StringIO()):
                self.assertEqual(main(["canonicalize", str(path)]), 2)


if __name__ == "__main__":
    unittest.main()

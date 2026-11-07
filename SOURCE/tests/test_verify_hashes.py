"""Unit tests for the synthetic-data SHA-256 verifier."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "verification"))
from verify_hashes import manifest_for, verify  # noqa: E402


class IntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "synthetic"
        self.root.mkdir()
        (self.root / "example.csv").write_text("id,value\n1,sample\n", encoding="utf-8")
        self.manifest = manifest_for(self.root)

    def test_unmodified_dataset_passes(self):
        result = verify(self.root, self.manifest)
        self.assertTrue(result["passed"])
        self.assertEqual(result["matched"], 1)

    def test_changed_file_is_detected(self):
        (self.root / "example.csv").write_text("id,value\n1,changed\n", encoding="utf-8")
        result = verify(self.root, self.manifest)
        self.assertEqual(result["modified"], ["example.csv"])
        self.assertFalse(result["passed"])

    def test_missing_and_unexpected_files_are_detected(self):
        (self.root / "example.csv").unlink()
        (self.root / "new.csv").write_text("new\n", encoding="utf-8")
        result = verify(self.root, self.manifest)
        self.assertEqual(result["missing"], ["example.csv"])
        self.assertEqual(result["unexpected"], ["new.csv"])
        self.assertFalse(result["passed"])

    def test_path_traversal_manifest_is_rejected(self):
        tampered = json.loads(json.dumps(self.manifest))
        tampered["files"][0]["path"] = "../outside.csv"
        with self.assertRaises(ValueError):
            verify(self.root, tampered)

    def test_symlink_is_rejected(self):
        try:
            (self.root / "linked.csv").symlink_to(self.root / "example.csv")
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks unavailable on this platform")
        with self.assertRaises(ValueError):
            manifest_for(self.root)


if __name__ == "__main__":
    unittest.main()

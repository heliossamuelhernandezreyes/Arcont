import json
import tempfile
import unittest
from pathlib import Path

from tools.arcont_hardening import check_maturity, sha256, validate_result


class HardeningTests(unittest.TestCase):
    def valid_result(self):
        return {
            "schema_version": 1,
            "benchmark_id": "ARC-BENCH-TEST-0001",
            "run_id": "run-1",
            "engine": {
                "name": "godot",
                "version": "4.7.2-stable",
                "commit": "ed1daf0bf001b61586d9930840f2f1394092c079",
            },
            "platform": {},
            "runtime": {},
            "experiment": {},
            "metrics": {},
            "provenance": {
                "harness_commit": "0" * 40,
                "raw_data_sha256": "a" * 64,
            },
            "aborted": False,
            "abort_reason": None,
        }

    def test_valid_result_passes(self):
        self.assertEqual(validate_result(self.valid_result()), [])

    def test_bad_commit_fails(self):
        obj = self.valid_result()
        obj["engine"]["commit"] = "bad"
        self.assertTrue(any("engine.commit" in e for e in validate_result(obj)))

    def test_aborted_requires_reason(self):
        obj = self.valid_result()
        obj["aborted"] = True
        self.assertTrue(any("abort_reason" in e for e in validate_result(obj)))

    def test_bad_hash_fails(self):
        obj = self.valid_result()
        obj["provenance"]["raw_data_sha256"] = "1234"
        self.assertTrue(any("raw_data_sha256" in e for e in validate_result(obj)))

    def test_maturity_cannot_overclaim(self):
        evidence = {
            "source_traced": True,
            "hypothesis": True,
            "observations": 1,
            "reproductions": 0,
            "hardware_profiles": 1,
            "engine_versions": 1,
            "validated_rule": False,
        }
        self.assertTrue(check_maturity("L7_VALIDATED_RULE", evidence))
        self.assertFalse(check_maturity("L3_OBSERVED", evidence))

    def test_sha256_is_byte_stable(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "data.bin"
            p.write_bytes(b"arcont")
            self.assertEqual(
                sha256(p),
                "64d9bcc1186e4980e8a36895171692353e58c92db3644a83e02610b3c6f9a445",
            )


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from pathlib import Path

from tools.arcont_hardening import check_maturity, max_maturity, maturity_missing, sha256, validate_result


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

    def l7_evidence(self):
        return {
            "source_traced": True,
            "hypothesis": True,
            "observations": 3,
            "reproductions": 3,
            "hardware_profiles": 2,
            "engine_versions": 2,
            "validated_rule": True,
            "limits_explicit": True,
            "contradictions_reviewed": True,
            "falsifiable": True,
            "decision_usefulness": True,
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

    def test_l3_requires_cumulative_source_and_hypothesis(self):
        evidence = {
            "source_traced": False,
            "hypothesis": False,
            "observations": 1,
        }
        errors = check_maturity("L3_OBSERVED", evidence)
        self.assertTrue(errors)
        self.assertIn("source_traced", errors[0])
        self.assertIn("hypothesis", errors[0])
        self.assertEqual(max_maturity(evidence), 0)

    def test_l7_cannot_be_reached_by_summary_flag_alone(self):
        evidence = {
            "source_traced": True,
            "hypothesis": True,
            "observations": 1,
            "reproductions": 0,
            "hardware_profiles": 1,
            "engine_versions": 1,
            "validated_rule": True,
        }
        errors = check_maturity("L7_VALIDATED_RULE", evidence)
        self.assertTrue(errors)
        self.assertLess(max_maturity(evidence), 7)
        self.assertIn("reproductions>=2", maturity_missing("L7_VALIDATED_RULE", evidence))
        self.assertIn("limits_explicit", maturity_missing("L7_VALIDATED_RULE", evidence))

    def test_complete_l7_evidence_passes(self):
        evidence = self.l7_evidence()
        self.assertEqual(check_maturity("L7_VALIDATED_RULE", evidence), [])
        self.assertEqual(max_maturity(evidence), 7)

    def test_cross_version_requires_cross_hardware_first(self):
        evidence = self.l7_evidence()
        evidence["hardware_profiles"] = 1
        self.assertTrue(check_maturity("L6_CROSS_VERSION", evidence))
        self.assertEqual(max_maturity(evidence), 4)

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

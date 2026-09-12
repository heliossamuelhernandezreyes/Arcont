import unittest

from tools.asset_trust import compatibility_level, validate_record_trust


class AssetTrustTests(unittest.TestCase):
    def record(self):
        return {
            "compatibility": {"godot": True, "android": True},
            "license": {"redistribution_allowed": True},
            "archive": {"mirrored_in_arcont": False},
            "review": {"license_verified": True},
        }

    def test_legacy_declared_compatibility_is_not_runtime_proof(self):
        record = self.record()
        self.assertEqual(compatibility_level(record, "godot"), "legacy-unverified")

    def test_format_evidence_is_distinct_from_runtime(self):
        record = self.record()
        record["compatibility_evidence"] = {
            "godot": {"level": "format", "basis": "glTF import path"}
        }
        self.assertEqual(compatibility_level(record, "godot"), "format")
        self.assertEqual(validate_record_trust(record), [])

    def test_runtime_evidence_requires_traceability(self):
        record = self.record()
        record["compatibility_evidence"] = {"android": {"level": "runtime"}}
        errors = validate_record_trust(record)
        self.assertTrue(any("tested_at" in e for e in errors))
        self.assertTrue(any("evidence_ref" in e for e in errors))

    def test_runtime_evidence_with_reference_passes(self):
        record = self.record()
        record["compatibility_evidence"] = {
            "android": {
                "level": "runtime",
                "tested_at": "2026-09-12T00:00:00Z",
                "evidence_ref": "ARC-EVIDENCE-ASSET-001",
            }
        }
        self.assertEqual(validate_record_trust(record), [])

    def test_mirroring_requires_verified_license(self):
        record = self.record()
        record["archive"]["mirrored_in_arcont"] = True
        record["review"]["license_verified"] = False
        self.assertTrue(any("license_verified" in e for e in validate_record_trust(record)))


if __name__ == "__main__":
    unittest.main()

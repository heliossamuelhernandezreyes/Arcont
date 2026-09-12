import tempfile
import unittest
from pathlib import Path

from tools.asset_vault_indexer import build_index, polyhaven_record, stable_id, validate_record


class AssetVaultIndexerTests(unittest.TestCase):
    def valid_record(self):
        return {
            "schema_version": 1,
            "id": "ARC-ASSET-TEST-0001",
            "title": "Test Asset",
            "asset_type": "3d_model",
            "dimensions": ["3d"],
            "themes": ["test"],
            "styles": [],
            "tags": ["prop"],
            "source": {
                "provider": "Test Provider",
                "author": None,
                "external_id": "asset-1",
                "asset_url": "https://example.invalid/a/asset-1",
                "download_url": None,
                "acquired_at": None,
            },
            "license": {
                "name": "CC0-1.0",
                "version": "1.0",
                "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
                "commercial_use": True,
                "modification": True,
                "attribution_required": False,
                "redistribution_allowed": True,
                "share_alike": False,
                "ai_training_allowed": True,
                "notes": None,
            },
            "technical": {"formats": []},
            "compatibility": {"godot": True, "unreal": True, "unity": True, "web": True, "android": True},
            "archive": {"mirrored_in_arcont": False, "local_path": None, "sha256": None, "size_bytes": None},
            "review": {"license_verified": True, "metadata_verified": True, "last_checked": None, "notes": None},
        }

    def test_valid_record_passes(self):
        self.assertEqual(validate_record(self.valid_record()), [])

    def test_mirror_requires_redistribution_right(self):
        record = self.valid_record()
        record["archive"]["mirrored_in_arcont"] = True
        record["license"]["redistribution_allowed"] = False
        errors = validate_record(record)
        self.assertTrue(any("redistribution_allowed" in e for e in errors))

    def test_bad_sha256_rejected(self):
        record = self.valid_record()
        record["archive"]["sha256"] = "bad"
        self.assertTrue(any("sha256" in e for e in validate_record(record)))

    def test_duplicate_source_identity_detected(self):
        import json
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalog = root / "assets" / "catalog" / "test"
            catalog.mkdir(parents=True)
            a = self.valid_record()
            b = self.valid_record()
            b["id"] = "ARC-ASSET-TEST-0002"
            (catalog / "a.asset.json").write_text(json.dumps(a), encoding="utf-8")
            (catalog / "b.asset.json").write_text(json.dumps(b), encoding="utf-8")
            _index, errors = build_index(root)
            self.assertTrue(any("duplicate source identity" in e for e in errors))

    def test_polyhaven_normalization_is_cc0_and_not_mirrored(self):
        record = polyhaven_record("test_asset", {"name": "Test", "type": "models", "tags": ["rock"], "polycount": 1234})
        self.assertEqual(record["license"]["name"], "CC0-1.0")
        self.assertTrue(record["license"]["commercial_use"])
        self.assertFalse(record["license"]["attribution_required"])
        self.assertFalse(record["archive"]["mirrored_in_arcont"])
        self.assertEqual(record["technical"]["triangle_count"], 1234)
        self.assertEqual(validate_record(record), [])

    def test_stable_id_is_deterministic(self):
        self.assertEqual(stable_id("POLYHAVEN", "abc"), stable_id("POLYHAVEN", "abc"))
        self.assertNotEqual(stable_id("POLYHAVEN", "abc"), stable_id("POLYHAVEN", "def"))


if __name__ == "__main__":
    unittest.main()

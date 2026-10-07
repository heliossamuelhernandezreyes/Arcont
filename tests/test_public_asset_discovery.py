import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.public_asset_discovery import (
    _canonical_sha,
    execute,
    files,
    search,
    stage,
)
from tools.project_bootstrap_control import bootstrap


def intent():
    return {
        "protocol": "arcont-project-intent",
        "version": 1,
        "project_id": "public_assets",
        "title": "Public Assets",
        "genre": "third-person action",
        "targets": ["Windows"],
        "asset_policy": {
            "user_assets": True,
            "public_assets": True,
            "commercial_use_required": True,
            "allow_network_discovery": True,
            "allowed_licenses": ["CC0"],
        },
    }


ASSETS = {
    "sunset_jhbcentral": {
        "name": "Joburg Central Sunset",
        "description": "City rooftop sunset",
        "category": "Streets & Town",
        "tags": ["city", "industrial", "sunset"],
        "authors": {"Greg Zaal": "Processing"},
        "download_count": 100,
        "files_hash": "provider-files-hash",
        "type": 0,
    },
    "dirty_football": {
        "name": "Dirty Football",
        "description": "Weathered soccer ball",
        "category": "Leisure",
        "tags": ["ball", "sport"],
        "authors": {"Example": "All"},
        "download_count": 20,
        "files_hash": "model-files-hash",
        "polycount": 37486,
        "type": 2,
    },
}

FILES = {
    "hdri": {
        "1k": {
            "hdr": {
                "url": "https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/1k/sunset_jhbcentral_1k.hdr",
                "size": 7,
                "md5": hashlib.md5(b"fixture", usedforsecurity=False).hexdigest(),
            }
        },
        "16k": {
            "hdr": {
                "url": "https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/16k+/sunset_jhbcentral_16k.hdr",
                "size": 999999999,
                "md5": "deadbeef",
            }
        },
    }
}


class PublicAssetDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name) / "game"
        self.project.mkdir()
        bootstrap(self.project, intent(), "godot-3d-minimal")

    def tearDown(self):
        self.tmp.cleanup()

    def fake_fetch(self, url, timeout=30):
        if "/files/" in url:
            return FILES
        return ASSETS

    @patch("tools.public_asset_discovery._fetch_json")
    def test_search_is_provider_scoped_and_license_explicit(self, fetch):
        fetch.side_effect = self.fake_fetch
        report = search(self.project, "sunset", "hdris", 5)
        self.assertTrue(report["ok"])
        self.assertFalse(report["write_performed"])
        self.assertEqual(report["result"]["count"], 1)
        row = report["result"]["results"][0]
        self.assertEqual(row["provider"], "polyhaven")
        self.assertEqual(row["provider_asset_id"], "sunset_jhbcentral")
        self.assertEqual(row["asset_license"], "CC0")
        self.assertTrue(row["commercial_use"])
        self.assertFalse(row["asset_attribution_required"])
        self.assertTrue(row["api_attribution_required"])

    @patch("tools.public_asset_discovery._fetch_json")
    def test_files_manifest_is_hashed_and_only_allowlisted_host_is_stageable(self, fetch):
        fetch.side_effect = self.fake_fetch
        report = files(self.project, "sunset_jhbcentral")
        self.assertTrue(report["ok"])
        self.assertEqual(report["result"]["manifest_sha256"], _canonical_sha(FILES))
        rows = {row["file_key"]: row for row in report["result"]["files"]}
        self.assertTrue(rows["hdri/1k/hdr"]["download_host_allowed"])
        self.assertTrue(rows["hdri/1k/hdr"]["stage_extension_allowed"])

    @patch("tools.public_asset_discovery._download")
    @patch("tools.public_asset_discovery._fetch_json")
    def test_stage_requires_manifest_binding_and_records_provenance(self, fetch, download):
        fetch.side_effect = self.fake_fetch

        def fake_download(url, target, expected_size, expected_md5):
            target.write_bytes(b"fixture")
            return {
                "bytes": 7,
                "sha256": hashlib.sha256(b"fixture").hexdigest(),
                "md5": hashlib.md5(b"fixture", usedforsecurity=False).hexdigest(),
            }

        download.side_effect = fake_download
        manifest = _canonical_sha(FILES)
        report = stage(
            self.project,
            {
                "semantic_id": "sky",
                "asset_id": "sunset_jhbcentral",
                "file_key": "hdri/1k/hdr",
                "manifest_sha256": manifest,
            },
        )
        self.assertTrue(report["ok"])
        record = report["result"]
        self.assertEqual(record["provider"], "Poly Haven")
        self.assertEqual(record["asset_license"], "CC0")
        self.assertEqual(record["provider_file_key"], "hdri/1k/hdr")
        self.assertEqual(record["files_manifest_sha256"], manifest)
        self.assertEqual(record["provenance_status"], "provider-api-and-download-integrity-verified")
        self.assertTrue((self.project / record["staged_path"]).is_file())
        stored = json.loads((self.project / ".arcont/assets/public/sky.asset.json").read_text())
        self.assertEqual(stored["sha256"], record["sha256"])

    @patch("tools.public_asset_discovery._fetch_json")
    def test_stage_fails_closed_when_manifest_changes(self, fetch):
        fetch.side_effect = self.fake_fetch
        with self.assertRaises(ValueError):
            stage(
                self.project,
                {
                    "semantic_id": "sky",
                    "asset_id": "sunset_jhbcentral",
                    "file_key": "hdri/1k/hdr",
                    "manifest_sha256": "0" * 64,
                },
            )

    @patch("tools.public_asset_discovery._fetch_json")
    def test_arbitrary_file_key_cannot_inject_url(self, fetch):
        fetch.side_effect = self.fake_fetch
        with self.assertRaises(ValueError):
            stage(
                self.project,
                {
                    "semantic_id": "evil",
                    "asset_id": "sunset_jhbcentral",
                    "file_key": "https://evil.example/payload",
                    "manifest_sha256": _canonical_sha(FILES),
                },
            )

    def test_public_asset_network_policy_is_required(self):
        denied = Path(self.tmp.name) / "denied"
        denied.mkdir()
        denied_intent = intent()
        denied_intent["project_id"] = "denied"
        denied_intent["asset_policy"]["allow_network_discovery"] = False
        bootstrap(denied, denied_intent, "godot-3d-minimal")
        with self.assertRaises(PermissionError):
            execute(
                denied,
                {
                    "protocol_version": 1,
                    "operation": "search",
                    "query": "city",
                    "asset_type": "all",
                    "limit": 5,
                },
            )

    def test_capabilities_do_not_allow_arbitrary_urls_or_archive_extraction(self):
        report = execute(self.project, {"protocol_version": 1, "operation": "capabilities"})
        self.assertTrue(report["ok"])
        self.assertFalse(report["arbitrary_url_download"])
        self.assertFalse(report["archive_extraction"])


if __name__ == "__main__":
    unittest.main()

import json
import tempfile
import unittest
from pathlib import Path

from tools.project_bootstrap_control import bootstrap
from tools.user_asset_intake import execute as asset_execute


def intent():
    return {
        "protocol": "arcont-project-intent",
        "version": 1,
        "project_id": "blank_game",
        "title": "Blank Game",
        "genre": "third-person action",
        "targets": ["Windows", "Android"],
        "visual_style": "dark industrial",
        "goals": ["Create a playable vertical slice"],
        "priorities": ["movement", "combat", "performance"],
        "performance": {"target_fps": 60, "resolution": "1280x720"},
        "asset_policy": {
            "user_assets": True,
            "public_assets": True,
            "commercial_use_required": True,
            "allow_network_discovery": False,
            "allowed_licenses": ["CC0", "MIT", "Custom-Commercial"],
        },
    }


class ProjectBootstrapAndAssetIntakeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "game"
        self.root.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def test_bootstrap_creates_external_godot_project_and_receipt(self):
        report = bootstrap(self.root, intent(), "godot-3d-minimal")
        self.assertTrue(report["ok"])
        self.assertTrue(report["write_performed"])
        self.assertTrue((self.root / "project.godot").is_file())
        self.assertTrue((self.root / "project.intent.json").is_file())
        self.assertTrue((self.root / "scenes/main.tscn").is_file())
        self.assertTrue((self.root / ".arcont/bootstrap.json").is_file())
        self.assertTrue((self.root / "incoming").is_dir())
        self.assertTrue((self.root / "authoring/recipes").is_dir())
        receipt = json.loads((self.root / ".arcont/bootstrap.json").read_text())
        self.assertEqual(receipt["template"], "godot-3d-minimal")
        self.assertEqual(receipt["project_id"], "blank_game")
        self.assertEqual(len(receipt["files"]["project.godot"]), 64)
        self.assertIn('run/main_scene="res://scenes/main.tscn"', (self.root / "project.godot").read_text())

    def test_bootstrap_supports_minimal_2d_without_embedding_arcont(self):
        report = bootstrap(self.root, intent(), "godot-2d-minimal")
        self.assertTrue(report["ok"])
        scene = (self.root / "scenes/main.tscn").read_text()
        self.assertIn('type="Node2D"', scene)
        self.assertNotIn("ARCONT repository", scene)
        self.assertFalse((self.root / ".git").exists())

    def test_bootstrap_refuses_nonempty_directory(self):
        (self.root / "keep.txt").write_text("user data")
        with self.assertRaises(ValueError):
            bootstrap(self.root, intent(), "godot-3d-minimal")
        self.assertEqual((self.root / "keep.txt").read_text(), "user data")

    def bootstrap_for_assets(self):
        bootstrap(self.root, intent(), "godot-3d-minimal")
        return self.root

    def test_user_asset_inspect_and_stage_preserve_hash_and_provenance(self):
        self.bootstrap_for_assets()
        source = self.root / "incoming/hero.svg"
        source.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="8" height="8"></svg>')
        inspected = asset_execute(
            self.root,
            {"protocol_version": 1, "operation": "inspect", "source": "incoming/hero.svg"},
        )
        self.assertTrue(inspected["ok"])
        self.assertEqual(inspected["result"]["kind"], "vector")
        self.assertFalse(inspected["result"]["rights_inferred"])

        staged = asset_execute(
            self.root,
            {
                "protocol_version": 1,
                "operation": "stage",
                "asset_id": "hero_icon",
                "source": "incoming/hero.svg",
                "rights": {
                    "basis": "user-owned",
                    "commercial_use": True,
                    "redistribution": False,
                    "license_name": None,
                    "attribution": None,
                    "notes": "Fixture owned by test user.",
                },
            },
        )
        self.assertTrue(staged["ok"])
        record = staged["result"]
        self.assertEqual(record["origin"], "user-provided")
        self.assertEqual(record["rights_status"], "user-declared-not-verified-by-arcont")
        self.assertEqual(record["sha256"], inspected["result"]["sha256"])
        self.assertTrue((self.root / record["staged_path"]).is_file())
        self.assertTrue((self.root / ".arcont/assets/user/hero_icon.asset.json").is_file())

        listed = asset_execute(self.root, {"protocol_version": 1, "operation": "list"})
        self.assertEqual(listed["result"]["count"], 1)
        self.assertEqual(listed["result"]["assets"][0]["id"], "hero_icon")

    def test_user_asset_source_cannot_escape_incoming(self):
        self.bootstrap_for_assets()
        (self.root / "outside.svg").write_text("<svg/>")
        with self.assertRaises(ValueError):
            asset_execute(
                self.root,
                {"protocol_version": 1, "operation": "inspect", "source": "outside.svg"},
            )

    def test_user_asset_stage_rejects_noncommercial_rights_when_project_requires_it(self):
        self.bootstrap_for_assets()
        (self.root / "incoming/music.ogg").write_bytes(b"OggSfixture")
        with self.assertRaises(ValueError):
            asset_execute(
                self.root,
                {
                    "protocol_version": 1,
                    "operation": "stage",
                    "asset_id": "music",
                    "source": "incoming/music.ogg",
                    "rights": {
                        "basis": "licensed",
                        "commercial_use": False,
                        "redistribution": False,
                        "license_name": "Custom-Commercial",
                    },
                },
            )

    def test_user_asset_stage_rejects_license_outside_project_allowlist(self):
        self.bootstrap_for_assets()
        (self.root / "incoming/mesh.glb").write_bytes(b"glTFfixture")
        with self.assertRaises(ValueError):
            asset_execute(
                self.root,
                {
                    "protocol_version": 1,
                    "operation": "stage",
                    "asset_id": "mesh",
                    "source": "incoming/mesh.glb",
                    "rights": {
                        "basis": "licensed",
                        "commercial_use": True,
                        "redistribution": True,
                        "license_name": "Unapproved-License",
                    },
                },
            )

    def test_archive_is_not_accepted_in_v1(self):
        self.bootstrap_for_assets()
        (self.root / "incoming/pack.zip").write_bytes(b"PKfixture")
        with self.assertRaises(ValueError):
            asset_execute(
                self.root,
                {"protocol_version": 1, "operation": "inspect", "source": "incoming/pack.zip"},
            )


if __name__ == "__main__":
    unittest.main()

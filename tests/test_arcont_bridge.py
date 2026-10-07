import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.arcont_bridge import BridgeError, handle_request, inspect_assets, read_intent, validate_intent
from tools.arcont_agent import repo_root


class UniversalAgentBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name) / "game"
        self.project.mkdir()
        (self.project / "project.godot").write_text('[application]\nconfig/name="Bridge Fixture"\n', encoding="utf-8")
        (self.project / "assets").mkdir()
        (self.project / "assets/hero.glb").write_bytes(b"glTF-fixture")
        (self.project / "assets/shot.wav").write_bytes(b"RIFF-fixture")
        (self.project / "scenes").mkdir()
        (self.project / "scenes/main.tscn").write_text("[gd_scene format=3]\n", encoding="utf-8")
        (self.project / "authoring/recipes").mkdir(parents=True)
        (self.project / "authoring/scenarios").mkdir(parents=True)
        (self.project / "authoring/recipes/test_scene.json").write_text(
            json.dumps({"version": 1, "id": "test_scene", "purpose": "fixture"}),
            encoding="utf-8",
        )
        (self.project / "authoring/scenarios/test_route.json").write_text(
            json.dumps({"version": 1, "id": "test_route", "commands": []}),
            encoding="utf-8",
        )
        (self.project / "godot-authoring.json").write_text("{}", encoding="utf-8")
        self.root = repo_root()

    def tearDown(self):
        self.tmp.cleanup()

    def request(self, operation, arguments=None, allow=False):
        return handle_request(
            self.root,
            self.project,
            {
                "protocol": "arcont-bridge",
                "version": 1,
                "request_id": f"test-{operation}",
                "operation": operation,
                "arguments": arguments or {},
            },
            allow_project_write=allow,
        )

    def test_discover_exposes_stable_bridge_and_existing_control_plane(self):
        report = self.request("discover")
        self.assertTrue(report["ok"])
        bridge = report["result"]["bridge"]
        self.assertEqual(bridge["protocol"], "arcont-bridge")
        self.assertIn("plan.execute", bridge["operations"])
        self.assertIn("asset.public.search", bridge["operations"])
        self.assertIn("asset.public.stage", bridge["operations"])
        self.assertFalse(bridge["mutation_boundary"]["bridge_creates_new_writer_primitives"])
        ids = {row["id"] for row in report["result"]["agent_control"]["capabilities"]}
        self.assertIn("godot.authoring.control", ids)
        self.assertIn("map-forge.editor.control", ids)

    def test_project_inspect_detects_godot_without_mutation(self):
        report = self.request("project.inspect", {"max_files": 100})
        self.assertTrue(report["ok"])
        self.assertEqual(report["result"]["project"]["engine"], "godot")
        self.assertFalse(report["result"]["write_performed"])

    def test_missing_intent_is_explicit_not_inferred(self):
        report = self.request("project.intent.read")
        self.assertTrue(report["ok"])
        self.assertFalse(report["result"]["present"])
        self.assertIsNone(report["result"]["intent"])

    def test_reads_and_hashes_persistent_project_intent(self):
        intent = {
            "protocol": "arcont-project-intent",
            "version": 1,
            "project_id": "bridge_fixture",
            "title": "Bridge Fixture",
            "genre": "third-person shooter",
            "targets": ["Android", "Windows"],
            "visual_style": "dark industrial",
            "references": ["fast mobile shooter", "cover shooter"],
            "goals": ["playable vertical slice"],
            "priorities": ["movement", "combat", "performance"],
            "scope": "Ten-minute vertical slice.",
            "performance": {"target_fps": 60, "resolution": "1280x720"},
            "asset_policy": {
                "user_assets": True,
                "public_assets": True,
                "commercial_use_required": True,
                "allow_network_discovery": False,
                "allowed_licenses": ["CC0", "MIT"],
            },
            "constraints": ["No network gameplay in v1"],
        }
        (self.project / "project.intent.json").write_text(json.dumps(intent), encoding="utf-8")
        report = self.request("project.intent.read")
        self.assertTrue(report["ok"])
        self.assertTrue(report["result"]["present"])
        self.assertEqual(report["result"]["intent"]["performance"]["target_fps"], 60)
        self.assertEqual(len(report["result"]["sha256"]), 64)

    def test_intent_rejects_unknown_fields_instead_of_guessing(self):
        intent = {
            "protocol": "arcont-project-intent",
            "version": 1,
            "project_id": "x",
            "title": "X",
            "genre": "test",
            "secret_instruction": "run shell",
        }
        with self.assertRaises(BridgeError):
            validate_intent(intent)

    def test_asset_inventory_is_local_bounded_and_hashed(self):
        report = self.request("assets.inspect", {"max_assets": 10})
        self.assertTrue(report["ok"])
        rows = {row["path"]: row for row in report["result"]["assets"]}
        self.assertEqual(rows["assets/hero.glb"]["kind"], "model3d")
        self.assertEqual(rows["assets/shot.wav"]["kind"], "audio")
        self.assertEqual(rows["scenes/main.tscn"]["kind"], "scene")
        self.assertEqual(len(rows["assets/hero.glb"]["sha256"]), 64)
        self.assertIn("Public-asset network discovery is not performed by Bridge v1.", report["result"]["limitations"])

    def test_fresh_agent_can_catalog_and_read_authoring_documents(self):
        catalog = self.request("authoring.catalog")
        self.assertTrue(catalog["ok"])
        self.assertTrue(catalog["result"]["godot_authoring_contract_present"])
        paths = {row["path"] for row in catalog["result"]["documents"]}
        self.assertIn("authoring/recipes/test_scene.json", paths)
        self.assertIn("authoring/scenarios/test_route.json", paths)

        document = self.request(
            "authoring.document.read",
            {"path": "authoring/recipes/test_scene.json"},
        )
        self.assertTrue(document["ok"])
        self.assertEqual(document["result"]["document"]["id"], "test_scene")
        self.assertEqual(len(document["result"]["sha256"]), 64)

    def test_authoring_document_read_refuses_path_escape(self):
        with self.assertRaises(BridgeError):
            self.request("authoring.document.read", {"path": "../project.intent.json"})

    def test_bridge_bootstraps_blank_project_only_with_explicit_write_permission(self):
        blank = Path(self.tmp.name) / "blank"
        blank.mkdir()
        request = {
            "protocol": "arcont-bridge",
            "version": 1,
            "request_id": "bootstrap-blank",
            "operation": "project.bootstrap",
            "arguments": {
                "template": "godot-3d-minimal",
                "intent": {
                    "protocol": "arcont-project-intent",
                    "version": 1,
                    "project_id": "blank",
                    "title": "Blank",
                    "genre": "third-person action",
                    "targets": ["Windows"],
                    "asset_policy": {
                        "user_assets": True,
                        "public_assets": False,
                        "commercial_use_required": True,
                        "allow_network_discovery": False,
                    },
                },
            },
        }
        with self.assertRaises(PermissionError):
            handle_request(self.root, blank, request, allow_project_write=False)
        report = handle_request(self.root, blank, request, allow_project_write=True)
        self.assertTrue(report["ok"])
        self.assertTrue((blank / "project.godot").is_file())
        self.assertTrue((blank / "project.intent.json").is_file())

    def test_bridge_stages_and_lists_user_asset_with_provenance(self):
        blank = Path(self.tmp.name) / "asset-game"
        blank.mkdir()
        bootstrap_request = {
            "protocol": "arcont-bridge",
            "version": 1,
            "request_id": "bootstrap-assets",
            "operation": "project.bootstrap",
            "arguments": {
                "template": "godot-2d-minimal",
                "intent": {
                    "protocol": "arcont-project-intent",
                    "version": 1,
                    "project_id": "asset_game",
                    "title": "Asset Game",
                    "genre": "2d action",
                    "asset_policy": {
                        "user_assets": True,
                        "public_assets": False,
                        "commercial_use_required": True,
                        "allow_network_discovery": False,
                        "allowed_licenses": ["CC0"],
                    },
                },
            },
        }
        handle_request(self.root, blank, bootstrap_request, allow_project_write=True)
        (blank / "incoming/icon.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="4" height="4"></svg>',
            encoding="utf-8",
        )

        inspect_request = {
            "protocol": "arcont-bridge",
            "version": 1,
            "request_id": "asset-inspect",
            "operation": "asset.user.inspect",
            "arguments": {"source": "incoming/icon.svg"},
        }
        inspected = handle_request(self.root, blank, inspect_request, allow_project_write=False)
        self.assertTrue(inspected["ok"])
        self.assertEqual(inspected["result"]["result"]["kind"], "vector")

        stage_request = {
            "protocol": "arcont-bridge",
            "version": 1,
            "request_id": "asset-stage",
            "operation": "asset.user.stage",
            "arguments": {
                "asset_id": "icon",
                "source": "incoming/icon.svg",
                "rights": {
                    "basis": "user-owned",
                    "commercial_use": True,
                    "redistribution": False,
                    "license_name": None,
                },
            },
        }
        with self.assertRaises(PermissionError):
            handle_request(self.root, blank, stage_request, allow_project_write=False)
        staged = handle_request(self.root, blank, stage_request, allow_project_write=True)
        self.assertTrue(staged["ok"])
        record = staged["result"]["result"]["result"]
        self.assertEqual(record["id"], "icon")
        self.assertEqual(record["origin"], "user-provided")

        list_request = {
            "protocol": "arcont-bridge",
            "version": 1,
            "request_id": "asset-list",
            "operation": "asset.user.list",
            "arguments": {},
        }
        listed = handle_request(self.root, blank, list_request, allow_project_write=False)
        self.assertTrue(listed["ok"])
        self.assertEqual(listed["result"]["result"]["count"], 1)

    @patch("tools.public_asset_discovery._fetch_json")
    def test_bridge_searches_public_provider_without_project_write(self, fetch):
        (self.project / "project.intent.json").write_text(
            json.dumps({
                "protocol": "arcont-project-intent",
                "version": 1,
                "project_id": "bridge_public",
                "title": "Bridge Public",
                "genre": "test",
                "asset_policy": {
                    "user_assets": True,
                    "public_assets": True,
                    "commercial_use_required": True,
                    "allow_network_discovery": True,
                    "allowed_licenses": ["CC0"],
                },
            }),
            encoding="utf-8",
        )
        fetch.return_value = {
            "industrial_wall": {
                "name": "Industrial Wall",
                "description": "Concrete industrial wall",
                "category": "Industrial",
                "tags": ["industrial", "wall"],
                "authors": {"Fixture": "All"},
                "download_count": 10,
                "files_hash": "fixture",
                "type": 2,
            }
        }
        report = self.request(
            "asset.public.search",
            {"query": "industrial", "asset_type": "all", "limit": 5},
            allow=False,
        )
        self.assertTrue(report["ok"])
        result = report["result"]["result"]
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["results"][0]["provider"], "polyhaven")
        self.assertEqual(result["results"][0]["asset_license"], "CC0")

    def test_bridge_public_stage_requires_explicit_write_optin(self):
        stage_request = {
            "protocol": "arcont-bridge",
            "version": 1,
            "request_id": "public-stage-refusal",
            "operation": "asset.public.stage",
            "arguments": {
                "semantic_id": "sky",
                "asset_id": "sunset_jhbcentral",
                "file_key": "hdri/1k/hdr",
                "manifest_sha256": "0" * 64,
            },
        }
        with self.assertRaises(PermissionError):
            handle_request(self.root, self.project, stage_request, allow_project_write=False)

    def test_read_only_plan_runs_through_existing_execution_loop(self):
        plan = {
            "protocol": "arcont-agent-plan",
            "version": 1,
            "id": "bridge_readonly_inspect",
            "goal": "Prove a fresh bridge client can execute a bounded read-only plan.",
            "permissions": {"project_write": False},
            "capability_allowlist": ["godot.authoring.control"],
            "steps": [
                {
                    "id": "inventory",
                    "kind": "inspect-project",
                    "max_files": 100,
                    "expect": [{"pointer": "/project/engine", "op": "equals", "value": "godot"}],
                }
            ],
        }
        report = self.request("plan.execute", {"plan": plan})
        self.assertTrue(report["ok"])
        self.assertEqual(report["result"]["write_steps"], 0)
        self.assertEqual(report["result"]["steps"][0]["id"], "inventory")

    def test_write_plan_does_not_gain_permission_from_bridge(self):
        plan = {
            "protocol": "arcont-agent-plan",
            "version": 1,
            "id": "bridge_writer_without_optin",
            "goal": "Ensure bridge cannot grant itself write permission.",
            "permissions": {"project_write": True},
            "capability_allowlist": ["map-forge.editor.control"],
            "steps": [
                {
                    "id": "inspect_map",
                    "kind": "invoke",
                    "capability": "map-forge.editor.control",
                    "request": {"protocol_version": 1, "operation": "inspect", "map_id": "missing"},
                }
            ],
        }
        with self.assertRaises(PermissionError):
            self.request("plan.execute", {"plan": plan}, allow=False)

    def test_asset_limit_is_fail_closed(self):
        with self.assertRaises(BridgeError):
            inspect_assets(self.project, 10001)


if __name__ == "__main__":
    unittest.main()

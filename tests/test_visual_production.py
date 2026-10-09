"""ARCONT Visual Production P0/P1 negative controls; no engine or external network."""
from __future__ import annotations
from copy import deepcopy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.visual_production_contract import validate_intent
from tools.visual_scene_inventory import inspect_scene

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / "templates/visual-production/industrial_arena.example.json").read_text(encoding="utf-8"))
SCHEMA = ROOT / "schemas/proposals/visual-production-intent.schema.json"


class VisualProductionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.project = Path(self.temp.name) / "game"
        (self.project / "maps").mkdir(parents=True)
        (self.project / "scenes").mkdir()
        self.map_file = self.project / "maps/test_foundry.json"
        self.map_file.write_text(json.dumps({"regions": [{"id": "entry_region"}, {"id": "core_region"}]}))
        self.scene_file = self.project / "scenes/demo.tscn"
        self.scene_file.write_text("""[gd_scene load_steps=3 format=3]

[ext_resource type="Script" path="res://scripts/runtime_scene.gd" id="1_script"]
[node name="World" type="Node3D"]
script = ExtResource("1_script")
[node name="Main Key" type="DirectionalLight3D" parent="."]
shadow_enabled = true
[node name="Floor" type="MeshInstance3D" parent="."]
mesh = SubResource("box")
""", encoding="utf-8")
        self.intent = deepcopy(FIXTURE)

    def tearDown(self):
        self.temp.cleanup()

    def validate(self):
        return validate_intent(self.intent, self.project)

    def test_schema_is_valid_and_example_passes(self):
        from jsonschema import Draft202012Validator
        Draft202012Validator.check_schema(json.loads(SCHEMA.read_text(encoding="utf-8")))
        problems, warnings = self.validate()
        self.assertEqual(problems, [])
        self.assertTrue(warnings)  # unmeasured / unpinned visual evidence

    def test_schema_rejects_missing_fields_and_unknown_keys(self):
        del self.intent["visual_kit"]
        self.intent["machine_exec"] = "sh -c echo no"
        self.assertTrue(self.validate()[0])

    def test_schema_rejects_project_write_optin(self):
        self.intent["approval"]["project_write_authorized"] = True
        self.assertTrue(any("project_write_authorized" in error for error in self.validate()[0]))

    def test_duplicate_zone_lighting_asset_and_camera_ids_fail(self):
        for name in ("zones", "lighting_profiles", "asset_roles", "capture_plan"):
            with self.subTest(name=name):
                original = self.intent[name]
                original.append(deepcopy(original[0]))
                self.assertTrue(any("duplicate id" in p for p in self.validate()[0]))
                original.pop()

    def test_unknown_zone_and_lighting_references_fail(self):
        self.intent["zones"][0]["lighting_profile_id"] = "invalid"
        self.intent["capture_plan"][1]["zone_id"] = "missing"
        errors = self.validate()[0]
        self.assertTrue(any("lighting profile" in e for e in errors))
        self.assertTrue(any("missing zone" in e for e in errors))

    def test_semantic_map_regions_and_hash_must_match(self):
        self.intent["zones"][0]["region_id"] = "not_in_map"
        self.intent["semantic_map"]["sha256"] = "0" * 64
        errors = self.validate()[0]
        self.assertTrue(any("SHA-256" in e for e in errors))
        self.assertTrue(any("unknown semantic region" in e for e in errors))
        self.intent["zones"][0]["region_id"] = "entry_region"
        self.intent["semantic_map"]["sha256"] = hashlib.sha256(self.map_file.read_bytes()).hexdigest()
        self.assertEqual(self.validate()[0], [])

    def test_traversal_or_symlink_map_refused(self):
        self.intent["semantic_map"]["path"] = "../../outside.json"
        self.assertTrue(self.validate()[0])
        self.intent["semantic_map"]["path"] = "maps/link.json"
        (self.project / "maps/link.json").symlink_to(Path(self.temp.name) / "outside.json")
        self.assertTrue(any("escapes" in e for e in self.validate()[0]))

    def test_staged_asset_without_provenance_refused(self):
        asset = self.intent["asset_roles"][0]
        asset.update(status="staged", sha256="a" * 64, source_record="records/missing.json")
        self.assertTrue(any("asset_roles" in e for e in self.validate()[0]))

    def test_staged_asset_hash_and_license_checked_against_bytes(self):
        asset = self.intent["asset_roles"][0]
        (self.project / "assets").mkdir()
        (self.project / "records").mkdir()
        obj = self.project / "assets/hero.glb"
        obj.write_bytes(b"verified cc0 example")
        sha = hashlib.sha256(obj.read_bytes()).hexdigest()
        receipt = self.project / "records/hero.json"
        receipt.write_text(json.dumps({"sha256": sha, "asset_license": "CC0", "staged_path": "assets/hero.glb"}))
        asset.update(status="staged", sha256=sha, source_record="records/hero.json")
        self.assertEqual(self.validate()[0], [])
        obj.write_bytes(b"tampered")
        self.assertTrue(any("staged asset bytes" in e for e in self.validate()[0]))
        obj.write_bytes(b"verified cc0 example")
        receipt.write_text(json.dumps({"sha256": sha, "asset_license": "restricted", "staged_path": "assets/hero.glb"}))
        self.assertTrue(any("license" in e for e in self.validate()[0]))

    def test_invalid_renderer_roi_and_fps_rejected(self):
        self.intent["render_profile"]["renderer"] = "forward_plus_hdr_gi"
        self.intent["capture_plan"][0]["roi"]["x"] = 0.9
        self.intent["budgets"]["fallback_fps"] = 90
        errors = self.validate()[0]
        self.assertTrue(any("unsupported" in e for e in errors))
        self.assertTrue(any("roi" in e for e in errors))
        self.assertTrue(any("fallback" in e for e in errors))

    def test_measured_budget_cannot_exist_without_external_trace(self):
        self.intent["budgets"]["measurement_status"] = "measured"
        self.assertTrue(any("hashed runtime trace" in e for e in self.validate()[0]))

    def test_scene_inspection_is_honest_about_dynamic_content(self):
        report = inspect_scene(self.project, "scenes/demo.tscn")
        self.assertEqual(report["static_source"]["node_count"], 3)
        self.assertEqual(report["static_source"]["light_count"], 1)
        self.assertEqual(report["static_source"]["mesh_node_count"], 1)
        self.assertEqual(report["static_source"]["external_script_paths"], ["res://scripts/runtime_scene.gd"])
        self.assertTrue(report["static_source"]["scripted_nodes"])
        self.assertIsNone(report["runtime"])
        self.assertFalse(report["runtime_complete"])
        self.assertFalse(report["writes_performed"])
        self.assertFalse(report["engine_executed"])
        self.assertTrue(any("Dynamic scripts" in msg for msg in report["limitations"]))

    def test_scene_inspection_rejects_escape_and_non_tscn(self):
        with self.assertRaises(ValueError):
            inspect_scene(self.project, "../../secrets.tscn")
        with self.assertRaises(ValueError):
            inspect_scene(self.project, "scenes/demo.gd")

    def test_snapshot_rejects_wrong_scene_hash(self):
        path = self.project / "snapshot.json"
        payload = self.snapshot()
        payload["scene_sha256"] = "0" * 64
        path.write_text(json.dumps(payload))
        with self.assertRaisesRegex(ValueError, "mismatch"):
            inspect_scene(self.project, "scenes/demo.tscn", snapshot=path)

    def snapshot(self):
        return {
            "protocol": "arcont-godot-scene-snapshot", "version": 1,
            "scene_path": "scenes/demo.tscn",
            "scene_sha256": hashlib.sha256(self.scene_file.read_bytes()).hexdigest(),
            "capture_source": "native-godot", "engine_version": "4.7.2-stable",
            "renderer": "gl_compatibility", "source_commit": "b" * 40,
            "nodes": [
                {"path": "World/Main Key", "type": "DirectionalLight3D", "shadow_enabled": True},
                {"path": "World/Floor", "type": "MeshInstance3D", "instance_count": 1,
                 "material_paths": ["res://materials/steel.tres"]},
                {"path": "World/Props", "type": "MultiMeshInstance3D", "instance_count": 33}
            ]
        }

    def test_snapshot_counts_real_supplied_tree_but_marks_unverified(self):
        path = self.project / "snapshot.json"
        path.write_text(json.dumps(self.snapshot()))
        report = inspect_scene(self.project, "scenes/demo.tscn", snapshot=path)
        self.assertEqual(report["runtime"]["light_count"], 1)
        self.assertEqual(report["runtime"]["reported_instances"], 34)
        self.assertEqual(report["runtime"]["material_paths_count"], 1)
        self.assertIn("unverified", report["runtime"]["evidence_status"])
        self.assertFalse(report["runtime_complete"])

    def test_snapshot_rejects_duplicate_nodes_and_forged_renderer(self):
        path = self.project / "snapshot.json"
        payload = self.snapshot()
        payload["nodes"].append(deepcopy(payload["nodes"][0]))
        path.write_text(json.dumps(payload))
        with self.assertRaisesRegex(ValueError, "duplicated"):
            inspect_scene(self.project, "scenes/demo.tscn", snapshot=path)
        payload = self.snapshot()
        payload["renderer"] = "forward_plus"
        path.write_text(json.dumps(payload))
        with self.assertRaisesRegex(ValueError, "renderer mismatch"):
            inspect_scene(self.project, "scenes/demo.tscn", self.intent, path)

    def test_production_script_remains_unchanged(self):
        before = self.scene_file.read_bytes()
        inspect_scene(self.project, "scenes/demo.tscn")
        self.assertEqual(before, self.scene_file.read_bytes())


if __name__ == "__main__":
    unittest.main()

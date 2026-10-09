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
from tools.visual_scene_diagnostics import analyze

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
        self.map_file.write_text(json.dumps({"anchors": [{"id":"entry_point","position":[0,0,0]},{"id":"core_point","position":[18,0,0]}], "regions": [{"id": "entry_region"}, {"id": "core_region"}]}))
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

    def test_bridge_discovers_readonly_visual_ops(self):
        from tools.arcont_bridge import discover
        manifest = discover(ROOT, self.project)
        operations = manifest["bridge"]["operations"]
        self.assertIn("visual.intent.validate", operations)
        self.assertIn("visual.scene.inventory", operations)
        self.assertIn("visual.scene.diagnose", operations)
        capability = {x["id"]: x for x in manifest["agent_control"]["capabilities"]}
        for name in ("visual.intent.validate", "visual.scene.inventory", "visual.scene.diagnose"):
            self.assertTrue(capability[name]["available"])
            self.assertEqual(capability[name]["access"], "read-only")

    def test_bridge_executes_visual_ops_without_write_optin(self):
        from tools.arcont_bridge import handle_request
        intent_file = self.project / "visual.intent.json"
        intent_file.write_text(json.dumps(self.intent))
        def invoke(op, args):
            return handle_request(ROOT, self.project, {
                "protocol":"arcont-bridge", "version":1,
                "request_id":"visual_ci", "operation":op, "arguments":args,
            }, allow_project_write=False)
        report = invoke("visual.intent.validate", {"path":"visual.intent.json"})
        self.assertTrue(report["ok"], report)
        self.assertFalse(report["result"]["writes_performed"])
        report = invoke("visual.scene.inventory", {"scene":"scenes/demo.tscn",
                                                   "intent_path":"visual.intent.json"})
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["result"]["static_source"]["node_count"], 3)
        self.assertFalse(report["result"]["engine_executed"])

    def test_bridge_diagnostic_is_readonly_and_bound_to_project(self):
        from tools.arcont_bridge import handle_request
        snapshot, visual_intent = self.diagnostic_fixture()
        reply = handle_request(ROOT, self.project, {
            "protocol":"arcont-bridge","version":1,"request_id":"diagnose",
            "operation":"visual.scene.diagnose",
            "arguments":{"scene":"scenes/demo.tscn","intent_path":visual_intent.name,
                         "snapshot_path":snapshot.name}
        }, allow_project_write=False)
        self.assertTrue(reply["ok"])
        self.assertEqual(reply["result"]["facts"]["all_light_count"],2)
        self.assertFalse(reply["result"]["writes_performed"])
        self.assertFalse(reply["result"]["engine_executed"])

    def test_bridge_refuses_visual_path_escape_and_argument_smuggling(self):
        from tools.arcont_bridge import handle_request, BridgeError
        req = {"protocol":"arcont-bridge","version":1,"request_id":"bad",
               "operation":"visual.intent.validate","arguments":{"path":"../../outside.json"}}
        with self.assertRaises(ValueError):
            handle_request(ROOT, self.project, req, allow_project_write=False)
        req["operation"] = "visual.scene.inventory"
        req["arguments"] = {"scene":"scenes/demo.tscn","execute_script":True}
        with self.assertRaises(BridgeError):
            handle_request(ROOT, self.project, req, allow_project_write=False)


    def test_sampling_anchor_cross_reference(self):
        self.intent["zones"][0]["anchor_id"] = "no_such_objective"
        errors, _ = self.validate()
        self.assertTrue(any("unknown semantic anchor" in x for x in errors))
        self.intent["zones"][0]["anchor_id"] = "entry_point"
        self.intent["zones"][0]["sample_radius_m"] = 8
        self.assertEqual(self.validate()[0], [])

    def diagnostic_fixture(self):
        native = self.snapshot()
        native["nodes"] = [
            {"path":"World/Light","type":"DirectionalLight3D",
             "world_position":[0,8,0],"shadow_enabled":True,
             "light_energy":1.2,"light_color":"ffffff"},
            {"path":"World/Art/Omni","type":"OmniLight3D",
             "world_position":[0,0,0],"shadow_enabled":False,
             "light_energy":2.2,"light_range":14,"light_color":"66aaff"},
            {"path":"World/Floor","type":"MeshInstance3D","world_position":[0,0,1],
             "instance_count":1,"geometry_type":"BoxMesh","material_paths":[],
             "material_descriptors":[{"kind":"StandardMaterial3D",
                                     "albedo_color":"aabbccff","roughness":0.5,
                                     "normal_enabled":True,"emission_enabled":False}]},
            {"path":"World/Art/Dressing","type":"MultiMeshInstance3D",
             "world_position":[0,0,2],"instance_count":30,"geometry_type":"ArrayMesh",
             "material_paths":[],"material_descriptors":[{"kind":"StandardMaterial3D",
                                 "albedo_color":"aabbccff","roughness":0.5,
                                 "normal_enabled":True,"emission_enabled":False}]},
            {"path":"World/Decor/Polygon","type":"MeshInstance3D",
             "world_position":[40,0,0],"instance_count":1,"geometry_type":"CylinderMesh",
             "material_paths":[],"material_descriptors":[{"kind":"StandardMaterial3D",
                                "albedo_color":"eeccbbff","normal_enabled":False,
                                "emission_enabled":True}]}
        ]
        file = self.project / "snapshot-diagnostics.json"
        file.write_text(json.dumps(native))
        self.intent["zones"][0]["anchor_id"] = "entry_point"
        self.intent["zones"][0]["sample_radius_m"] = 8
        self.intent["zones"][1]["anchor_id"] = "core_point"
        intent_file = self.project / "visual.intent.json"
        intent_file.write_text(json.dumps(self.intent))
        return file, intent_file

    def test_diagnostic_metrics_and_zone_sampling(self):
        path, intent = self.diagnostic_fixture()
        report = analyze(self.project, "scenes/demo.tscn", path, intent)
        self.assertTrue(report["ok"])
        facts = report["facts"]
        self.assertEqual(facts["node_count"], 5)
        self.assertEqual(facts["mesh_nodes"], 3)
        self.assertEqual(facts["total_mesh_instances"], 32)
        self.assertEqual(facts["materials"]["observed_descriptors"], 3)
        self.assertEqual(facts["materials"]["unique_parameter_signatures"], 2)
        self.assertEqual(facts["local_light_count"], 1)
        self.assertEqual(facts["shadowed_light_count"], 1)
        self.assertEqual(report["zones"][0]["mesh_centers_in_radius"], 2)
        self.assertEqual(report["zones"][0]["lights_reaching_anchor"], 1)
        self.assertEqual(report["zones"][1]["lights_reaching_anchor"], 0)
        self.assertTrue(any(w["code"]=="ZONE_WITHOUT_LOCAL_LIGHT_AT_ANCHOR" for w in report["budget_warnings"]))
        self.assertFalse(report["writes_performed"])
        self.assertEqual(report["evidence_status"], "externally_supplied_runtime_snapshot_unverified")

    def test_diagnostics_reject_invalid_positions_and_snapshot_hash(self):
        path, intent = self.diagnostic_fixture()
        native = json.loads(path.read_text())
        native["nodes"][1]["world_position"] = [float("nan"),0,0]
        path.write_text(json.dumps(native))
        with self.assertRaisesRegex(ValueError, "finite"):
            analyze(self.project, "scenes/demo.tscn", path, intent)
        native = self.snapshot()
        native["scene_sha256"] = "f"*64
        path.write_text(json.dumps(native))
        with self.assertRaisesRegex(ValueError, "mismatch"):
            analyze(self.project, "scenes/demo.tscn", path, intent)

    def test_diagnostics_warn_on_art_stage_collision_nodes(self):
        path, intent = self.diagnostic_fixture()
        native = json.loads(path.read_text())
        native["nodes"].append({"path":"World/cinematic industrial dressing/CollisionShape3D",
                                "type":"CollisionShape3D"})
        path.write_text(json.dumps(native))
        report=analyze(self.project, "scenes/demo.tscn", path, intent)
        self.assertEqual(report["facts"]["total_suspicious_colliders"],1)
        self.assertTrue(any(w["code"]=="PHYSICS_INSIDE_RENDER_STAGES" for w in report["budget_warnings"]))



if __name__ == "__main__":
    unittest.main()

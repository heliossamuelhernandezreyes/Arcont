import copy
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

from tools.production_assets import digest, stage, validate_plan
from tools.production_recipes import animation_profile, sector
from tools.production_evidence import summarize, compare
from tools.production_toolchain import doctor


class ProductionTests(unittest.TestCase):
    def test_doctor_rejects_component_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); (root/"tool.py").write_text("accepted")
            manifest={"release":"fixture","components":[{"id":"fixture","files":{"tool.py":digest(root/"tool.py")}}],"limits":[]}
            (root/"production-toolchain.json").write_text(json.dumps(manifest))
            self.assertTrue(doctor(root)["ok"])
            (root/"tool.py").write_text("changed")
            self.assertEqual(doctor(root)["failures"],["tool.py"])

    def project(self, root):
        doc={"asset":{"version":"2.0"},"accessors":[{"count":3,"type":"VEC3"}],
             "meshes":[{"primitives":[{"attributes":{"POSITION":0}}]}],
             "buffers":[{"uri":"mesh.bin","byteLength":36}],"images":[{"uri":"texture.png"}]}
        (root/"model.gltf").write_text(json.dumps(doc)); (root/"mesh.bin").write_bytes(bytes(36)); (root/"texture.png").write_bytes(b"fixture")
        proof={"sources":[{"name":"Fixture","license":"CC0-1.0","url":"https://example.invalid/reviewed"}],
               "delivered_files":[{"path":p,"sha256":digest(root/p)} for p in ["model.gltf","mesh.bin","texture.png"]]}
        (root/"proof.json").write_text(json.dumps(proof))
        return {"version":1,"id":"fixture","provenance_manifest":"proof.json","provenance_sha256":digest(root/"proof.json"),
                "assets":[{"id":"prop.fixture","path":"model.gltf","source_name":"Fixture","budget":{"triangles_max":10,"materials_max":2}}]}

    def test_staging_copies_complete_dependency_closure_and_repeats(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); plan=self.project(root)
            before={p:digest(root/p) for p in ["model.gltf","mesh.bin","texture.png"]}
            result=stage(root,plan,"assets/candidates")
            self.assertEqual(result,stage(root,plan,"assets/candidates"))
            self.assertEqual(set(result["files"]),set(before))
            for p,sha in before.items():
                self.assertEqual(digest(root/result["bundle_directory"]/p),sha)
                self.assertEqual(digest(root/p),sha)

    def test_source_change_and_candidate_corruption_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); plan=self.project(root); result=stage(root,plan,"assets/candidates")
            (root/result["bundle_directory"]/"mesh.bin").write_bytes(b"changed")
            with self.assertRaises(ValueError): stage(root,plan,"assets/candidates")
            (root/"model.gltf").write_text('{}')
            with self.assertRaises(ValueError): validate_plan(root,plan)

    def test_unverified_dependency_and_escape_fail_before_bundle_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); plan=self.project(root)
            (root/"texture.png").write_bytes(b"changed")
            with self.assertRaises(ValueError): stage(root,plan,"assets/candidates")
            self.assertFalse((root/"assets/candidates").exists())
            plan["assets"][0]["path"]="../model.gltf"
            with self.assertRaises(ValueError): validate_plan(root,plan)

    def test_dependency_uri_cannot_escape_model_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); plan=self.project(root)
            model=json.loads((root/"model.gltf").read_text()); model["buffers"][0]["uri"]="%2e%2e/escape.bin"
            (root/"model.gltf").write_text(json.dumps(model))
            with self.assertRaises(ValueError): validate_plan(root,plan)

    def test_budget_and_unknown_license_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); plan=self.project(root); plan["assets"][0]["budget"]["triangles_max"]=0
            with self.assertRaises(ValueError): validate_plan(root,plan)

    def test_ambiguous_license_and_triangle_strip_do_not_bypass_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); plan=self.project(root)
            proof=json.loads((root/"proof.json").read_text()); proof["sources"][0]["license"]="not CC0"
            (root/"proof.json").write_text(json.dumps(proof)); plan["provenance_sha256"]=digest(root/"proof.json")
            with self.assertRaises(ValueError): validate_plan(root,plan)
            plan=self.project(root); model=json.loads((root/"model.gltf").read_text())
            model["meshes"][0]["primitives"][0]["mode"]=5
            (root/"model.gltf").write_text(json.dumps(model))
            proof=json.loads((root/"proof.json").read_text()); proof["delivered_files"][0]["sha256"]=digest(root/"model.gltf")
            (root/"proof.json").write_text(json.dumps(proof)); plan["provenance_sha256"]=digest(root/"proof.json")
            with self.assertRaises(ValueError): validate_plan(root,plan)
            plan=self.project(root); proof=json.loads((root/"proof.json").read_text()); proof["sources"][0]["license"]="unknown"
            (root/"proof.json").write_text(json.dumps(proof)); plan["provenance_sha256"]=digest(root/"proof.json")
            with self.assertRaises(ValueError): validate_plan(root,plan)

    def layout(self):
        return {"version":1,"id":"yard","floor":{"size":[20,20]},
                "covers":[{"id":"cover","position":[-3,0],"size":[2,1.1,.5],"vaultable":True}],
                "routes":[{"id":"centre","clearance_radius":.45,"points":[[0,8],[0,-8]]},
                          {"id":"side","clearance_radius":.45,"points":[[5,8],[5,-8]]}]}

    def test_diagonal_route_clearance_detects_intersection_between_waypoints(self):
        recipe=self.layout(); self.assertTrue(sector(recipe)["ok"])
        recipe["routes"][0]["points"]=[[-8,8],[2,-8]]
        with self.assertRaises(ValueError): sector(recipe)

    def test_sector_rejects_low_ceiling_height_claim_and_nonfinite_coordinates(self):
        recipe=self.layout(); recipe["covers"][0]["size"][1]=2
        with self.assertRaises(ValueError): sector(recipe)
        recipe=self.layout(); recipe["routes"][0]["points"][0][0]=float('nan')
        with self.assertRaises(ValueError): sector(recipe)

    def test_animation_map_must_be_bijective(self):
        profile={"version":1,"bone_map":{"a":"root","b":"root"},"clips":["idle"],"translation_scale":1}
        with self.assertRaises(ValueError): animation_profile(profile)

    def record(self):
        return {"scope":"linux-rendered","device":"fixture","engine":"4.7.2","renderer":"GL","resolution":[1280,720],
                "build":"test","scenario":"yard","warmup_frames":30,"frame_wall_ms":[10]*99+[100]}

    def test_distribution_preserves_tail_and_scope(self):
        record=self.record(); result=summarize(record)
        self.assertEqual(result["p95_ms"],10); self.assertEqual(result["max_ms"],100)
        self.assertEqual(result["measurement_scope"],"linux-rendered")
        self.assertNotIn("target_device_validated",result)

    def test_compare_refuses_different_devices_and_nan_samples(self):
        first=self.record(); second=copy.deepcopy(first); second["scope"]="android-device"
        with self.assertRaises(ValueError): compare(first,second)
        first["frame_wall_ms"][0]=float('nan')
        with self.assertRaises(ValueError): summarize(first)


if __name__=="__main__": unittest.main()

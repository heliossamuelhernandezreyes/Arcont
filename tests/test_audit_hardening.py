"""Regression coverage for the independently reproduced October 29 audit."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from tools import arcont_agent as agent, arcont_bridge as bridge
from tools import development_session as sessions, godot_structured_editing as editing
from tools import map_forge_control as maps
from tools.acceptance_contract import validate_criterion, verify_criterion
from tools.capability_matrix import validate as validate_matrix
from tools.model_forge_validate import validate_report
from tools.png_integrity import decode_rgba
from tools.png_sprite_audit import _decode_rgba_png as audit_png
from tools.png_sprite_normalize import _decode_rgba_png as normalize_png, _encode_rgba_png
from tools.project_bootstrap_control import bootstrap

ROOT = Path(__file__).resolve().parents[1]


def intent():
    return {"protocol": "arcont-project-intent", "version": 1,
            "project_id": "audit", "title": "Audit", "genre": "2d"}


class AuditHardeningTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def game(self):
        path = self.root / "game"
        path.mkdir()
        bootstrap(path, intent(), "godot-2d-minimal")
        return path

    def request(self, project, operation, arguments):
        return bridge.handle_request(ROOT, project, {"protocol": "arcont-bridge", "version": 1,
            "request_id": "audit", "operation": operation, "arguments": arguments}, allow_project_write=False)

    def test_read_aliases_cannot_dispatch_any_writer_before_engine_execution(self):
        game = self.game()
        before = {p.relative_to(game): p.read_bytes() for p in game.rglob("*") if p.is_file()}
        with patch.object(editing, "execute", side_effect=AssertionError("engine dispatch reached")):
            for alias in ("godot.structured.validate", "godot.script.inspect"):
                for inner in bridge.DIRECT_WRITE_OPERATIONS:
                    with self.subTest(alias=alias, inner=inner), self.assertRaises(ValueError):
                        self.request(game, alias, {"operation": inner, "path": "scripts/probe.gd", "source": "extends Node\n"})
                with self.assertRaises(ValueError):
                    self.request(game, alias, {"protocol_version": 1})
        self.assertEqual(before, {p.relative_to(game): p.read_bytes() for p in game.rglob("*") if p.is_file()})

    def test_writer_permissions_are_checked_before_dispatch(self):
        game = self.game()
        with patch.object(bridge, "invoke_capability", side_effect=AssertionError("writer invoked")):
            with self.assertRaises(PermissionError):
                self.request(game, "godot.script.create", {"path": "scripts/a.gd", "source": "extends Node\n", "if_revision": None})

    def test_structured_unknown_fields_and_missing_fields_fail_closed(self):
        game = self.game()
        for op, args in [("godot.structured.validate", {"allow_project_write": True}),
                         ("godot.script.inspect", {}), ("project.inspect", {"unexpected": 1})]:
            with self.subTest(op=op), self.assertRaises(ValueError):
                self.request(game, op, args)

    def test_intent_and_authoring_refuse_external_symlink_ancestors(self):
        game = self.game()
        outside = self.root / "outside.json"
        outside.write_text(json.dumps(intent()))
        (game / "project.intent.json").unlink()
        (game / "project.intent.json").symlink_to(outside)
        with self.assertRaises(ValueError):
            self.request(game, "project.intent.read", {})
        shutil.rmtree(game / "authoring/recipes")
        (game / "authoring/recipes").symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.request(game, "authoring.catalog", {})

    def test_all_png_consumers_reject_bad_crc_missing_end_and_expansion(self):
        raw = _encode_rgba_png(2, 2, [bytes([1, 2, 3, 255] * 2)] * 2)
        bad_crc = bytearray(raw)
        bad_crc[-13] ^= 1
        path = self.root / "frame.png"
        for name, data in [("crc", bytes(bad_crc)), ("end", raw[:-12]), ("trailing", raw + b"extra")]:
            path.write_bytes(data)
            for reader in (lambda: decode_rgba(path), lambda: audit_png(path, 8), lambda: normalize_png(path)):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    reader()

    def test_validate_rejects_non_executable_engine(self):
        game = self.game()
        binary = self.root / "fake-godot"
        binary.write_text("not an executable")
        with patch.dict(os.environ, {"GODOT_BIN": str(binary)}):
            result = editing.respond(game, {"protocol_version": 1, "operation": "validate"})
        self.assertFalse(result["ok"])

    def test_runtime_without_executor_is_not_available(self):
        row = next(r for r in agent.capability_snapshot(ROOT)["capabilities"] if r["id"] == "runtime-lab.execute")
        self.assertFalse(row["available"])
        self.assertEqual(row["availability_status"], "external-unconfigured")

    def test_empty_and_malformed_model_reports_are_not_approved(self):
        profile = {"id": "audit", "budgets": {"triangles_max": 100, "materials_max": 2}}
        for report in ({}, {"assets": []}, {"assets": [None]}):
            with self.subTest(report=report), self.assertRaises(ValueError):
                validate_report(report, profile)
        for bad in (True, -1, float("nan"), "3"):
            result = validate_report({"assets": [{"path": "a.glb", "gltf_version": "2.0", "triangles": bad, "materials": 1}]}, profile)
            self.assertFalse(result["ok"])

    def test_runtime_criterion_cannot_be_defined_as_inventory(self):
        with self.assertRaises(ValueError):
            validate_criterion({"description": "combat", "verification_level": "runtime",
                "checks": [{"kind": "inspect-project", "expect": [{"pointer": "/project/engine", "op": "equals", "value": "godot"}]}]})

    def test_inventory_cannot_satisfy_playtest_and_wrong_result_does_not_pass(self):
        criterion = validate_criterion({"description": "Combat playtest", "verification_level": "runtime", "checks": [{
            "kind": "invoke", "capability": "godot.authoring.control", "operation": "playtest",
            "request_match": {"document_id": "combat"},
            "expect": [{"pointer": "/result/passed", "op": "equals", "value": True}]}]})
        step = {"id": "inventory", "kind": "inspect-project", "ok": True,
                "output": {"project": {"engine": "godot"}}}
        self.assertFalse(verify_criterion(criterion, [step])[0])
        step.update(kind="invoke", capability="godot.authoring.control",
                    resolved_request={"operation": "playtest", "document_id": "combat"},
                    output={"result": {"passed": False}})
        self.assertFalse(verify_criterion(criterion, [step])[0])
        step["output"]["result"]["passed"] = True
        self.assertTrue(verify_criterion(criterion, [step])[0])
        step["output"]["result"]["passed"] = 1
        self.assertFalse(verify_criterion(criterion, [step])[0])
        step["output"]["result"]["passed"] = True
        step["resolved_request"]["document_id"] = "unrelated"
        self.assertFalse(verify_criterion(criterion, [step])[0])

    def test_legacy_text_cannot_complete_a_session(self):
        game = self.game()
        cfg = {"id": "audit", "goal": "Audit", "capability_allowlist": ["godot.structured.control"],
               "permissions": {"project_write": True},
               "milestones": [{"id": "combat", "goal": "Combat", "acceptance": ["Defeat enemy and save"]}]}
        state = sessions.create(game, {"spec": cfg})["result"]["session"]
        plan = {"protocol": "arcont-agent-plan", "version": 1, "id": "inventory", "goal": "Inventory",
                "permissions": {"project_write": False}, "capability_allowlist": ["godot.structured.control"],
                "steps": [{"id": "inventory", "kind": "inspect-project", "expect": [{"pointer": "/project/engine", "op": "equals", "value": "godot"}]}]}
        with patch.object(sessions, "execute_plan", side_effect=AssertionError("plan must not run")):
            with self.assertRaises(sessions.SessionError):
                sessions.execute_one(game, {"session_id": "audit", "if_session_revision": state["revision"],
                    "milestone_id": "combat", "plan": plan, "complete_milestone": True,
                    "completion_evidence": [{"criterion_index": 0, "step_ids": ["inventory"]}]})

    def test_indeterminate_process_termination_pauses_and_preserves_pending_review(self):
        game = self.game()
        cfg = {"id": "uncertain", "goal": "Audit", "capability_allowlist": ["godot.structured.control"],
               "permissions": {"project_write": True},
               "milestones": [{"id": "work", "goal": "Work", "acceptance": ["Review required"]}]}
        state = sessions.create(game, {"spec": cfg})["result"]["session"]
        plan = {"protocol": "arcont-agent-plan", "version": 1, "id": "attempt", "goal": "Attempt",
                "permissions": {"project_write": False}, "capability_allowlist": ["godot.structured.control"],
                "steps": [{"id": "inventory", "kind": "inspect-project"}]}
        request = {"session_id": "uncertain", "if_session_revision": state["revision"],
                   "milestone_id": "work", "plan": plan, "complete_milestone": False}
        with patch.object(sessions, "execute_plan", return_value={"ok": False, "status": "indeterminate",
            "steps_completed": 1, "write_steps": 0, "steps": []}) as run:
            response = sessions.execute_one(game, request)
            current = response["result"]["session"]
            self.assertEqual(current["status"], "paused")
            self.assertIsNotNone(sessions.inspect(game, {"session_id": "uncertain"})["result"]["pending_run"])
            request["if_session_revision"] = current["revision"]
            with self.assertRaises(sessions.SessionError):
                sessions.execute_one(game, request)
            self.assertEqual(run.call_count, 1)

    def test_imported_helper_and_project_adapter_changes_invalidate_pins(self):
        snapshot = self.root / "arcont"
        shutil.copytree(ROOT / "tools", snapshot / "tools", ignore=shutil.ignore_patterns("__pycache__"))
        for relative in ("arcont.manifest.json", "processors.lock.json", "integrations/mcp/package-lock.json"):
            target = snapshot / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        registry = agent.load_registry(ROOT)
        with patch.object(sessions, "arcont_root", return_value=snapshot):
            before = sessions._toolchain_sha(registry, ["godot.structured.control"])
            helper = snapshot / "tools/project_lock.py"
            helper.write_text(helper.read_text() + "\n# changed helper\n")
            self.assertNotEqual(before, sessions._toolchain_sha(registry, ["godot.structured.control"]))
        game = self.game()
        (game / "tools").mkdir()
        adapter = game / "tools/adapter.py"
        adapter.write_text("print('first')")
        (game / "godot-authoring.json").write_text(json.dumps({"adapter_command": [sys.executable, "tools/adapter.py"]}))
        before = sessions._project_execution_sha(game)
        adapter.write_text("print('second')")
        self.assertNotEqual(before, sessions._project_execution_sha(game))

    def test_matrix_detects_implemented_feature_reported_missing(self):
        snapshot = self.root / "matrix"
        paths = ["docs/knowledge/GODOT_2D_CAPABILITY_MATRIX.yaml", "tools/png_sprite_normalize.py",
                 "tools/png_sprite_audit.py", "tests/test_png_sprite_normalize.py", "tests/test_png_sprite_audit.py"]
        for relative in paths:
            target = snapshot / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        self.assertTrue(validate_matrix(snapshot)["ok"])
        path = snapshot / paths[0]
        path.write_text(path.read_text().replace("      - deterministic_atlas_builder", "      - normalization_tool\n      - deterministic_atlas_builder"))
        self.assertFalse(validate_matrix(snapshot)["ok"])

    @unittest.skipUnless(sys.platform.startswith("linux"), "Linux subreaper acceptance")
    def test_supervisor_maps_proc_pids_into_its_own_namespace(self):
        from tools.process_supervisor import _descendants
        child = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(10)"])
        try:
            self.assertIn(child.pid, _descendants())
        finally:
            child.terminate()
            child.wait(timeout=5)

    @unittest.skipUnless(sys.platform.startswith("linux"), "Linux subreaper acceptance")
    def test_timeout_cancels_detached_adapter_before_any_late_write(self):
        project = self.root / "timeout"
        project.mkdir()
        adapter = project / "adapter.py"
        adapter.write_text("import json,sys,time\nfrom pathlib import Path\njson.load(sys.stdin)\ntime.sleep(1.8)\nPath('late').write_text('late')\nprint(json.dumps({'ok':True}))\n")
        (project / "godot-authoring.json").write_text(json.dumps({"protocol_version": 1,
            "adapter_command": [sys.executable, str(adapter)], "timeout_seconds": 10}))
        result = agent.invoke_capability(ROOT, "godot.authoring.control", project,
            {"protocol_version": 1, "operation": "discover"}, True, 1)
        self.assertEqual(result["status"], "timeout")
        self.assertTrue(result["process_tree_terminated"])
        time.sleep(1.2)
        self.assertFalse((project / "late").exists())

    def test_map_publication_crash_never_exposes_mixed_generations(self):
        project = self.root / "map"
        project.mkdir()
        (project / "map-forge.authoring.json").write_text('{"protocol_version":1}')
        editor = maps.Editor(project)
        old = {"map": {"id": "world", "generation": "old"}, "physical": {"map_id": "world", "generation": "old"}}
        new = {"map": {"id": "world", "generation": "new"}, "physical": {"map_id": "world", "generation": "new"}}
        editor.commit("world", None, old, None)
        for phase in ("generation", "head"):
            code = '''import json,os,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from tools import map_forge_control as m
p=Path(sys.argv[2]); e=m.Editor(p); before=e.read('world')
after={'map':{'id':'world','generation':'new'},'physical':{'map_id':'world','generation':'new'}}
original=m.atomic_write
def crash(path,value):
 original(path,value)
 if (sys.argv[3]=='head' and Path(path).parent==e.head_dir) or (sys.argv[3]=='generation' and value==after): os._exit(73)
m.atomic_write=crash
e.commit('world',before,after,m.revision(before))
'''
            run = subprocess.run([sys.executable, "-c", code, str(ROOT), str(project), phase], timeout=10)
            self.assertEqual(run.returncode, 73)
            observed = editor.read("world")
            self.assertEqual(observed["map"]["generation"], observed["physical"]["generation"])
            self.assertEqual(observed, old if phase == "generation" else new)
        # OS lock was released on abrupt exit; another legitimate commit works.
        editor.commit("world", new, old, maps.revision(new))
        self.assertEqual(editor.read("world"), old)


@unittest.skipUnless(os.environ.get("GODOT_BIN"), "set GODOT_BIN for native class registry acceptance")
class NativeAuditTests(unittest.TestCase):
    def test_imported_class_can_be_replaced_and_invalid_edit_preserves_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            bootstrap(project, intent(), "godot-2d-minimal")
            path = project / "scripts/hero.gd"
            source = "class_name AuditHero\nextends Node2D\nfunc value():\n    return 1\n"
            create = editing.respond(project, {"protocol_version": 1, "operation": "script.create", "path": "scripts/hero.gd", "source": source, "if_revision": None})
            self.assertTrue(create["ok"], create)
            run = subprocess.run([os.environ["GODOT_BIN"], "--headless", "--path", str(project), "--editor", "--import", "--quit"], capture_output=True, timeout=30)
            self.assertEqual(run.returncode, 0)
            changed = editing.respond(project, {"protocol_version": 1, "operation": "script.replace", "path": "scripts/hero.gd", "source": source.replace("return 1", "return 2"), "if_revision": hashlib.sha256(path.read_bytes()).hexdigest()})
            self.assertTrue(changed["ok"], changed)
            self.assertIn("return 2", path.read_text())
            before = path.read_bytes()
            invalid = editing.respond(project, {"protocol_version": 1, "operation": "script.replace", "path": "scripts/hero.gd", "source": "class_name AuditHero\nextends DOES_NOT_EXIST\n", "if_revision": hashlib.sha256(before).hexdigest()})
            self.assertFalse(invalid["ok"])
            self.assertEqual(before, path.read_bytes())


if __name__ == "__main__":
    unittest.main()

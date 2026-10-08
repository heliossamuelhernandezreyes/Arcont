import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "arcont_agent.py"
spec = importlib.util.spec_from_file_location("arcont_agent", MODULE_PATH)
agent = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(agent)


class ArcontAgentTests(unittest.TestCase):
    def make_root(self, tmp: str) -> Path:
        root = Path(tmp)
        (root / "tools").mkdir()
        (root / "arcont.manifest.json").write_text(
            json.dumps({
                "arcont_version": "1.0.0",
                "repository_role": "lab",
                "production_game_code_allowed": False,
                "embedded_godot_project_allowed": False,
            }), encoding="utf-8"
        )
        return root

    def test_capabilities_report_guards_and_missing_entrypoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_root(tmp)
            (root / "agent.capabilities.json").write_text(json.dumps({
                "schema_version": 1,
                "protocol": "arcont-agent-control",
                "capabilities": [
                    {"id": "ok", "access": "read-only", "entrypoint": "tools/ok.py", "argv": []},
                    {"id": "missing", "access": "read-only", "entrypoint": "tools/missing.py", "argv": []},
                ],
            }), encoding="utf-8")
            (root / "tools" / "ok.py").write_text("print('{}')\n", encoding="utf-8")
            report = agent.capability_snapshot(root)
            self.assertFalse(report["guards"]["production_game_code_allowed"])
            rows = {row["id"]: row for row in report["capabilities"]}
            self.assertTrue(rows["ok"]["available"])
            self.assertFalse(rows["missing"]["available"])

    def test_doctor_runs_only_whitelisted_doctor_capabilities(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_root(tmp)
            (root / "agent.capabilities.json").write_text(json.dumps({
                "schema_version": 1,
                "protocol": "arcont-agent-control",
                "capabilities": [
                    {"id": "check", "access": "read-only", "entrypoint": "tools/check.py", "argv": [], "doctor": True},
                    {"id": "skip", "access": "read-only", "entrypoint": "tools/skip.py", "argv": [], "doctor": False},
                ],
            }), encoding="utf-8")
            (root / "tools" / "check.py").write_text(
                "import json; print(json.dumps({'ok': True, 'value': 7}))\n", encoding="utf-8"
            )
            (root / "tools" / "skip.py").write_text("raise SystemExit(9)\n", encoding="utf-8")
            report = agent.run_diagnostics(root, 5)
            self.assertTrue(report["ok"])
            self.assertEqual([row["id"] for row in report["results"]], ["check"])
            self.assertEqual(report["results"][0]["stdout"]["value"], 7)

    def test_doctor_refuses_non_read_only_doctor_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_root(tmp)
            (root / "agent.capabilities.json").write_text(json.dumps({
                "schema_version": 1,
                "protocol": "arcont-agent-control",
                "capabilities": [{"id": "runtime", "access": "external-runtime", "doctor": True}],
            }), encoding="utf-8")
            report = agent.run_diagnostics(root, 5)
            self.assertFalse(report["ok"])
            self.assertEqual(report["results"][0]["status"], "refused-non-read-only")

    def test_project_inspection_is_bounded_and_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "project.godot").write_text("[application]\n", encoding="utf-8")
            (project / "scripts").mkdir()
            (project / "scripts" / "player.gd").write_text("extends Node\n", encoding="utf-8")
            (project / "art").mkdir()
            (project / "art" / "hero.png").write_bytes(b"png")
            (project / "model.glb").write_bytes(b"glb")
            report = agent.inspect_project(project, 100)
            info = report["project"]
            self.assertEqual(info["engine"], "godot")
            self.assertEqual(info["categories"]["source"], 1)
            self.assertEqual(info["categories"]["assets_2d"], 1)
            self.assertEqual(info["categories"]["assets_3d"], 1)
            self.assertFalse(report["write_performed"])

    def test_invoke_requires_explicit_project_write_permission(self):
        with tempfile.TemporaryDirectory() as root_tmp, tempfile.TemporaryDirectory() as project_tmp:
            root = self.make_root(root_tmp)
            (root / "agent.capabilities.json").write_text(json.dumps({
                "schema_version": 1,
                "protocol": "arcont-agent-control",
                "capabilities": [{
                    "id": "writer",
                    "access": "external-project-write",
                    "entrypoint": "tools/writer.py",
                    "doctor": False,
                    "invocable": True,
                }],
            }), encoding="utf-8")
            (root / "tools" / "writer.py").write_text("print('{\"ok\": true}')\n", encoding="utf-8")
            with self.assertRaises(PermissionError):
                agent.invoke_capability(root, "writer", Path(project_tmp), {"protocol_version": 1}, False, 5)

    def test_invoke_runs_registered_external_writer_with_json_request(self):
        with tempfile.TemporaryDirectory() as root_tmp, tempfile.TemporaryDirectory() as project_tmp:
            root = self.make_root(root_tmp)
            (root / "agent.capabilities.json").write_text(json.dumps({
                "schema_version": 1,
                "protocol": "arcont-agent-control",
                "capabilities": [{
                    "id": "writer",
                    "access": "external-project-write",
                    "entrypoint": "tools/writer.py",
                    "doctor": False,
                    "invocable": True,
                    "project_arg": "--project",
                    "request_arg": "--request",
                }],
            }), encoding="utf-8")
            (root / "tools" / "writer.py").write_text(
                "import argparse,json,sys\n"
                "p=argparse.ArgumentParser();p.add_argument('--project');p.add_argument('--request');a=p.parse_args()\n"
                "req=json.loads(sys.stdin.read());print(json.dumps({'ok': True, 'project': a.project, 'operation': req.get('operation')}))\n",
                encoding="utf-8",
            )
            report = agent.invoke_capability(
                root,
                "writer",
                Path(project_tmp),
                {"protocol_version": 1, "operation": "inspect"},
                True,
                5,
            )
            self.assertTrue(report["ok"])
            self.assertEqual(report["permission"], "explicit-project-write")
            self.assertEqual(report["result"]["operation"], "inspect")
            self.assertEqual(Path(report["result"]["project"]), Path(project_tmp).resolve())

    def test_invoke_rejects_project_embedded_inside_arcont(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_root(tmp)
            project = root / "embedded-game"
            project.mkdir()
            (root / "agent.capabilities.json").write_text(json.dumps({
                "schema_version": 1,
                "protocol": "arcont-agent-control",
                "capabilities": [{
                    "id": "writer",
                    "access": "external-project-write",
                    "entrypoint": "tools/writer.py",
                    "doctor": False,
                    "invocable": True,
                }],
            }), encoding="utf-8")
            (root / "tools" / "writer.py").write_text("print('{\"ok\": true}')\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                agent.invoke_capability(root, "writer", project, {"protocol_version": 1}, True, 5)

    def test_registry_rejects_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_root(tmp)
            (root / "agent.capabilities.json").write_text(json.dumps({
                "schema_version": 1,
                "protocol": "arcont-agent-control",
                "capabilities": [
                    {"id": "same", "access": "read-only"},
                    {"id": "same", "access": "read-only"},
                ],
            }), encoding="utf-8")
            with self.assertRaises(ValueError):
                agent.load_registry(root)


if __name__ == "__main__":
    unittest.main()

import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools.godot_authoring_control import Authoring, ControlError, respond
from tools.godot_authoring_mcp import dispatch


class AuthoringTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "adapter.py").write_text(
            'import sys,json,pathlib\np=json.load(sys.stdin); r=p.get("recipe") or {}\n'
            'd=pathlib.Path(p["output_directory"]); (d/"scene.tscn").write_text("built " + str(r.get("steps")))\n'
            'print(json.dumps({"ok":not r.get("fail",False),"engine":"test adapter"}))\n')
        (self.root / "godot-authoring.json").write_text(json.dumps({"protocol_version": 1, "adapter_command": [sys.executable, "adapter.py"]}))
        self.editor = Authoring(self.root)
        self.recipe = {"version": 1, "id": "city", "steps": [{"id": "floor", "op": "new", "class": "Node3D"}]}

    def tearDown(self):
        self.temp.cleanup()

    def request(self, operation, **kwargs):
        return self.editor.execute({"protocol_version": 1, "operation": operation, "document_id": "city", **kwargs})

    def create(self):
        return self.request("create", recipe=self.recipe, dry_run=False)

    def test_dry_run_builds_evidence_without_publishing(self):
        result = self.request("create", recipe=self.recipe)
        self.assertTrue(result["ok"])
        self.assertFalse(result["committed"])
        self.assertIsNone(self.editor.read("city"))
        directory = self.root / result["evidence"]["directory"]
        self.assertTrue((directory / "scene.tscn").is_file())
        artifact = next(x for x in result["evidence"]["manifest"]["artifacts"] if x["path"] == "scene.tscn")
        self.assertEqual(artifact["sha256"], hashlib.sha256((directory / "scene.tscn").read_bytes()).hexdigest())

    def test_full_patch_restore_and_immutable_previous_bundle(self):
        created = self.create()
        old = (self.root / created["evidence"]["directory"] / "scene.tscn").read_bytes()
        changed = self.request("patch", if_revision=created["revision"], dry_run=False,
                               patch=[{"op": "add", "path": "/steps/@floor/properties", "value": {"arbitrary": True}}])
        self.assertNotEqual(created["revision"], changed["revision"])
        self.assertEqual(old, (self.root / created["evidence"]["directory"] / "scene.tscn").read_bytes())
        restored = self.request("restore", if_revision=changed["revision"], restore_revision=created["revision"], dry_run=False)
        self.assertEqual(created["revision"], restored["revision"])
        self.assertEqual(self.recipe, self.editor.read("city")["recipe"])
        self.assertNotEqual(created["evidence"]["directory"], restored["evidence"]["directory"])

    def test_stale_revision_rejected_before_engine(self):
        self.create()
        with patch.object(self.editor, "adapter") as adapter:
            with self.assertRaises(ControlError):
                self.request("patch", if_revision="stale", patch=[])
            adapter.assert_not_called()

    def test_engine_failure_preserves_source_and_bundle(self):
        created = self.create()
        before = self.editor.path("city").read_bytes()
        recipe = {**self.recipe, "fail": True}
        result = self.request("replace", if_revision=created["revision"], recipe=recipe, dry_run=False)
        self.assertFalse(result["ok"])
        self.assertFalse(result["committed"])
        self.assertEqual(before, self.editor.path("city").read_bytes())
        self.assertTrue((self.root / created["evidence"]["directory"] / "scene.tscn").is_file())

    def test_failed_publication_preserves_atomic_head(self):
        created = self.create()
        before = self.editor.path("city").read_bytes()
        from tools.godot_authoring_control import atomic_write
        def fail_head(path, value):
            if path == self.editor.path("city"):
                raise OSError("disk full")
            return atomic_write(path, value)
        with patch("tools.godot_authoring_control.atomic_write", side_effect=fail_head):
            with self.assertRaises(OSError):
                self.request("patch", if_revision=created["revision"], dry_run=False,
                             patch=[{"op": "add", "path": "/label", "value": "change"}])
        self.assertEqual(before, self.editor.path("city").read_bytes())

    def test_lock_covers_build_and_commit(self):
        with self.editor.lock("city"):
            with self.assertRaises(ControlError):
                self.create()
        self.assertTrue(self.create()["ok"])

    @unittest.skipUnless(os.name == "posix", "SIGKILL recovery requires POSIX")
    def test_killed_process_releases_authoring_lock(self):
        import select
        code = ('import sys\nfrom tools.godot_authoring_control import Authoring\n'
                'with Authoring(sys.argv[1]).lock("city"):\n'
                ' print("locked", flush=True)\n'
                ' sys.stdin.read()\n')
        process = subprocess.Popen([sys.executable, "-c", code, str(self.root)],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            self.assertTrue(select.select([process.stdout], [], [], 5)[0], "child never acquired lock")
            self.assertEqual(process.stdout.readline().strip(), b"locked")
            with self.assertRaises(ControlError): self.create()
            process.kill()
            process.communicate(timeout=5)
            # The persistent inode and an old empty lock file are harmless.
            self.assertTrue(self.create()["ok"])
        finally:
            if process.poll() is None: process.kill()
            process.communicate(timeout=5)

    def test_symlink_outputs_and_escaped_paths_rejected(self):
        for identifier in ["../city", "/city", "x/y"]:
            with self.assertRaises(ControlError): self.editor.path(identifier)
        (self.root / "outside.txt").write_text("external")
        (self.root / "adapter.py").write_text('import sys,json,pathlib\np=json.load(sys.stdin); d=pathlib.Path(p["output_directory"]); (d/"escape").symlink_to(pathlib.Path.cwd()/"outside.txt"); print(json.dumps({"ok":True}))')
        with self.assertRaises(ControlError): self.create()
        self.assertIsNone(self.editor.read("city"))

    def test_dependencies_can_be_inspected_and_repaired_after_change(self):
        dependency = self.root / "input.gd"
        dependency.write_text("old")
        self.recipe["dependencies"] = {"input.gd": hashlib.sha256(b"old").hexdigest()}
        created = self.create()
        dependency.write_text("new")
        self.assertEqual(created["revision"], self.request("inspect")["revision"])
        with self.assertRaises(ControlError): self.request("build", if_revision=created["revision"])
        result = self.request("patch", if_revision=created["revision"], dry_run=False,
                              patch=[{"op": "replace", "path": "/dependencies/input.gd", "value": hashlib.sha256(b"new").hexdigest()}])
        self.assertTrue(result["committed"])

    def test_duplicate_ids_and_nonboolean_dry_run_rejected(self):
        recipe = copy.deepcopy(self.recipe)
        recipe["steps"].append(recipe["steps"][0])
        with self.assertRaises(ControlError): self.request("create", recipe=recipe)
        with self.assertRaises(ControlError): self.request("create", recipe=self.recipe, dry_run="false")

    def test_history_corruption_rejected(self):
        created = self.create()
        (self.root / ".arcont/history/city" / (created["revision"] + ".json")).write_text(json.dumps({**self.recipe, "changed": True}))
        with self.assertRaises(ControlError):
            self.request("restore", if_revision=created["revision"], restore_revision=created["revision"])

    def test_mcp_and_cli_share_the_same_controls(self):
        result = dispatch(self.root, {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                     "params": {"name": "arcont_authoring", "arguments": {"protocol_version": 1, "operation": "capabilities"}}})
        response = json.loads(result["result"]["content"][0]["text"])
        self.assertTrue(response["ok"])
        self.assertIn("patch", response["operations"])
        self.assertIsNone(dispatch(self.root, {"jsonrpc": "2.0", "method": "notifications/initialized"}))
        error = dispatch(self.root, {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "unknown"}})
        self.assertEqual(error["error"]["code"], -32602)
        init = dispatch(self.root, {"jsonrpc": "2.0", "id": 3, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}})
        self.assertEqual(init["result"]["protocolVersion"], "2025-06-18")

    def test_response_envelope_reports_invalid_requests(self):
        self.assertFalse(respond(self.root, {"operation": "create"})["ok"])

    def playtest_fixture(self, passed=True):
        created = self.create()
        (self.root / "runner.gd").write_text("trusted project runner")
        config = {"protocol_version": 1, "adapter_command": [sys.executable, "adapter.py"],
                  "playtest": {"script": "res://runner.gd"}}
        (self.root / "godot-authoring.json").write_text(json.dumps(config))
        self.editor = Authoring(self.root)
        (self.root / "adapter.py").write_text(
            'import sys,json,pathlib\np=json.load(sys.stdin)\n'
            'd=pathlib.Path(p["output_directory"]); (d/"trace.json").write_text("[]")\n'
            'print(json.dumps({"ok":True,"steps":[{"id":"playtest_session","value":{"passed":' + str(passed) + '}}]}))\n')
        session = {"version": 1, "id": "route", "actor": "Actors/Explorer", "commands": [{"id": "walk", "frames": 60, "actions": {"forward": 1}}]}
        return created, session

    def test_playtest_reads_accepted_artifact_without_publishing_head(self):
        created, session = self.playtest_fixture(passed=False)
        before = self.editor.path("city").read_bytes()
        result = self.request("playtest", if_revision=created["revision"], if_bundle=created["evidence"]["directory"], scene="scene.tscn", session=session)
        self.assertTrue(result["ok"])
        self.assertFalse(result["passed"])
        self.assertFalse(result["committed"])
        self.assertEqual(self.editor.path("city").read_bytes(), before)
        self.assertEqual(result["revision"], created["revision"])
        self.assertEqual(result["source_bundle"], created["evidence"]["directory"])
        self.assertTrue((self.root / result["evidence"]["directory"] / "trace.json").exists())

    def test_playtest_rejects_tampered_scene_before_engine(self):
        created, session = self.playtest_fixture()
        (self.root / created["evidence"]["directory"] / "scene.tscn").write_text("changed accepted scene")
        with patch.object(self.editor, "adapter") as adapter:
            with self.assertRaises(ControlError): self.request("playtest", if_revision=created["revision"], if_bundle=created["evidence"]["directory"], scene="scene.tscn", session=session)
            adapter.assert_not_called()

    def test_playtest_rejects_unrecorded_scene_and_invalid_session(self):
        created, session = self.playtest_fixture()
        for scene in ["../scene.tscn", "/scene.tscn", "unrecorded.tscn"]:
            with self.assertRaises(ControlError): self.request("playtest", if_revision=created["revision"], if_bundle=created["evidence"]["directory"], scene=scene, session=session)
        session["commands"][0]["frames"] = 10**12
        with patch.object(self.editor, "adapter") as adapter:
            with self.assertRaises(ControlError): self.request("playtest", if_revision=created["revision"], if_bundle=created["evidence"]["directory"], scene="scene.tscn", session=session)
            adapter.assert_not_called()

    def test_capabilities_only_advertises_existing_contained_runner(self):
        created, session = self.playtest_fixture()
        configurations = [None, [], "runner", {}, {"script": 42},
                          {"script": "runner.gd"}, {"script": "user://runner.gd"},
                          {"script": "res://runner.txt"}, {"script": "res://missing.gd"},
                          {"script": "res://../outside.gd"}, {"script": "res://."}]
        request = {"protocol_version": 1, "operation": "playtest", "document_id": "city",
                   "if_revision": created["revision"], "if_bundle": created["evidence"]["directory"],
                   "scene": "scene.tscn", "session": session}
        for configuration in configurations:
            with self.subTest(configuration=configuration):
                self.editor.config["playtest"] = configuration
                self.assertFalse(self.request("capabilities")["playtest_available"])
                with patch.object(self.editor, "adapter") as adapter:
                    with self.assertRaises(ControlError): self.editor.execute(request)
                    adapter.assert_not_called()
        self.editor.config["playtest"] = {"script": "res://runner.gd"}
        self.assertTrue(self.request("capabilities")["playtest_available"])
        (self.root / "runner.gd").unlink()
        self.assertFalse(self.request("capabilities")["playtest_available"])

    def test_playtest_rejects_stale_bundle_after_same_revision_rebuild(self):
        created, session = self.playtest_fixture()
        runner_adapter = (self.root / "adapter.py").read_text()
        (self.root / "adapter.py").write_text(
            'import sys,json,pathlib\np=json.load(sys.stdin)\n'
            'd=pathlib.Path(p["output_directory"]); (d/"scene.tscn").write_text("different rebuild output")\n'
            'print(json.dumps({"ok":True}))\n')
        rebuilt = self.request("build", if_revision=created["revision"], dry_run=False)
        self.assertEqual(created["revision"], rebuilt["revision"])
        self.assertNotEqual(created["evidence"]["directory"], rebuilt["evidence"]["directory"])
        (self.root / "adapter.py").write_text(runner_adapter)
        with patch.object(self.editor, "adapter") as adapter:
            for bundle in [None, 42, created["evidence"]["directory"]]:
                with self.subTest(bundle=bundle), self.assertRaisesRegex(ControlError, "bundle conflict"):
                    self.request("playtest", if_revision=created["revision"], if_bundle=bundle,
                                 scene="scene.tscn", session=session)
            adapter.assert_not_called()
        inspected = self.request("inspect")
        result = self.request("playtest", if_revision=inspected["revision"],
                              if_bundle=inspected["last_build"]["directory"], scene="scene.tscn", session=session)
        self.assertTrue(result["passed"])
        self.assertEqual(result["source_bundle"], rebuilt["evidence"]["directory"])

    def test_malformed_failed_adapter_steps_preserve_cli_and_mcp_evidence(self):
        created, session = self.playtest_fixture()
        request = {"protocol_version": 1, "operation": "playtest", "document_id": "city",
                   "if_revision": created["revision"], "if_bundle": created["evidence"]["directory"],
                   "scene": "scene.tscn", "session": session}
        before = self.editor.path("city").read_bytes()
        for steps in [None, 42, "failure", {"error": "failed"}, [None, 42, "failed"]]:
            with self.subTest(steps=steps):
                failure = {"ok": False, "error": "engine failure", "steps": steps}
                (self.root / "adapter.py").write_text(
                    'import sys,json\njson.load(sys.stdin)\nprint(' + repr(json.dumps(failure)) + ')\n')
                response = dispatch(self.root, {"jsonrpc": "2.0", "id": 42, "method": "tools/call",
                                               "params": {"name": "arcont_authoring", "arguments": request}})
                self.assertEqual(response["id"], 42)
                self.assertTrue(response["result"]["isError"])
                observed = json.loads(response["result"]["content"][0]["text"])
                self.assertFalse(observed["ok"])
                self.assertFalse(observed["passed"])
                self.assertIsNone(observed["report"])
                self.assertEqual(observed["result"], failure)
                self.assertTrue((self.root / observed["evidence"]["directory"] / "response.json").is_file())
        tool = Path(__file__).resolve().parents[1] / "tools/godot_authoring_control.py"
        cli = subprocess.run([sys.executable, str(tool), "--project", str(self.root)],
                             input=json.dumps(request), text=True, capture_output=True, timeout=10)
        self.assertEqual(cli.returncode, 1)
        self.assertNotIn("Traceback", cli.stderr)
        self.assertIn("evidence", json.loads(cli.stdout))
        self.assertEqual(before, self.editor.path("city").read_bytes())

    def test_mcp_advertises_bundle_pin(self):
        response = dispatch(self.root, {"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        properties = response["result"]["tools"][0]["inputSchema"]["properties"]
        self.assertEqual(properties["if_bundle"], {"type": "string"})


if __name__ == "__main__":
    unittest.main()

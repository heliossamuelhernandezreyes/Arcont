#!/usr/bin/env python3
"""Revisioned authoring jobs for arbitrary Godot nodes, resources and provider APIs.

The project owns the engine adapter. ARCONT owns job execution, history and the
single atomic head pointer. Engine output is built in a fresh immutable bundle.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import uuid

if __package__:
    from .map_forge_control import ControlError, apply_patch, atomic_write, changes, decode, encoded, revision
    from .playtest_contract import validate as validate_playtest
else:
    from map_forge_control import ControlError, apply_patch, atomic_write, changes, decode, encoded, revision
    from playtest_contract import validate as validate_playtest

OPERATIONS = ("capabilities", "discover", "list", "inspect", "create", "replace", "patch", "restore", "build", "playtest")
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")


class Authoring:
    def __init__(self, project):
        self.root = Path(project).resolve()
        self.config = decode((self.root / "godot-authoring.json").read_text(encoding="utf-8"))
        if self.config.get("protocol_version") != 1:
            raise ControlError("unsupported authoring protocol")
        self.heads = self.contained(self.config.get("document_directory", "authoring/documents"))
        self.history = self.contained(".arcont/history")
        self.runs = self.contained(".arcont/runs")

    def contained(self, relative):
        if not isinstance(relative, str) or Path(relative).is_absolute():
            raise ControlError("expected a project-relative path")
        result = (self.root / relative).resolve()
        if self.root not in result.parents:
            raise ControlError("path escapes project or addresses its root")
        return result

    def path(self, identifier):
        if not isinstance(identifier, str) or not IDENTIFIER.fullmatch(identifier):
            raise ControlError("invalid document_id")
        return self.contained(str(self.heads.relative_to(self.root) / (identifier + ".json")))

    def read(self, identifier):
        path = self.path(identifier)
        if not path.exists():
            return None
        head = decode(path.read_text(encoding="utf-8"))
        if not isinstance(head, dict) or revision(head.get("recipe")) != head.get("revision"):
            raise ControlError("corrupt authoring head")
        self.validate(head["recipe"], identifier, dependencies=False)
        return head

    def validate(self, recipe, identifier, dependencies=True):
        if not isinstance(recipe, dict) or recipe.get("version") != 1 or recipe.get("id") != identifier:
            raise ControlError("recipe requires version=1 and id=document_id")
        steps = recipe.get("steps")
        if not isinstance(steps, list) or not all(isinstance(s, dict) and isinstance(s.get("op"), str) for s in steps):
            raise ControlError("recipe.steps must contain explicit operation objects")
        ids = [s["id"] for s in steps if "id" in s]
        if not all(isinstance(i, str) and IDENTIFIER.fullmatch(i) for i in ids) or len(ids) != len(set(ids)):
            raise ControlError("step ids must be safe, unique identifiers")
        pins = recipe.get("dependencies", {})
        if not isinstance(pins, dict):
            raise ControlError("dependencies must map project-relative paths to SHA-256")
        for relative, digest in pins.items():
            if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise ControlError("dependency requires SHA-256")
            path = self.contained(relative)
            if dependencies and (not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest):
                raise ControlError("dependency changed or missing: " + relative)
        encoded(recipe)

    @contextlib.contextmanager
    def lock(self, identifier):
        path = self.contained(".arcont/locks/" + identifier + ".lock")
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise ControlError("document is being operated on; retry after completion") from exc
        os.close(fd)
        try:
            yield
        finally:
            path.unlink(missing_ok=True)

    def adapter(self, operation, recipe, options, identifier):
        argv = self.config.get("adapter_command")
        if not isinstance(argv, list) or not argv or not all(isinstance(a, str) for a in argv):
            raise ControlError("adapter_command must be an argv array")
        directory = self.contained(str(self.runs.relative_to(self.root) / identifier / uuid.uuid4().hex))
        directory.mkdir(parents=True)
        payload = {"protocol_version": 1, "operation": operation, "recipe": recipe,
                   "options": options, "output_directory": str(directory)}
        atomic_write(directory / "request.json", payload)
        process = subprocess.Popen(argv, cwd=self.root, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True, start_new_session=os.name == "posix")
        try:
            stdout, stderr = process.communicate(encoded(payload), timeout=int(self.config.get("timeout_seconds", 240)))
        except BaseException:
            if os.name == "posix":
                os.killpg(process.pid, signal.SIGKILL)
            else:
                process.kill()
            process.communicate()
            atomic_write(directory / "failure.json", {"ok": False, "error": "adapter interrupted or timed out"})
            raise
        (directory / "adapter.stderr.log").write_text(stderr, encoding="utf-8")
        try:
            result = decode(stdout)
        except (ValueError, TypeError) as exc:
            (directory / "adapter.stdout.log").write_text(stdout, encoding="utf-8")
            raise ControlError("adapter returned invalid JSON; evidence: " + str(directory)) from exc
        if not isinstance(result, dict):
            raise ControlError("adapter result must be an object")
        if process.returncode != 0 or result.get("ok") is not True:
            result["ok"] = False
        atomic_write(directory / "response.json", result)
        artifacts = []
        for path in sorted(directory.rglob("*")):
            if path.is_symlink() or directory not in path.resolve().parents:
                raise ControlError("adapter output contains a symlink or escaped artifact")
            if path.is_file():
                artifacts.append({"path": str(path.relative_to(directory)), "bytes": path.stat().st_size,
                                  "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        manifest = {"ok": result["ok"], "recipe_revision": revision(recipe) if recipe else None,
                    "artifacts": artifacts, "result": result}
        atomic_write(directory / "manifest.json", manifest)
        return result, {"directory": str(directory.relative_to(self.root)), "manifest": manifest}

    def execute(self, request):
        if not isinstance(request, dict) or request.get("protocol_version") != 1:
            raise ControlError("request requires protocol_version=1")
        operation = request.get("operation")
        if operation not in OPERATIONS:
            raise ControlError("unsupported authoring operation")
        if operation == "capabilities":
            return {"ok": True, "operations": list(OPERATIONS), "configuration": self.config,
                    "playtest_available": isinstance(self.config.get("playtest"), dict),
                    "arbitrary_engine_apis": True, "dry_run_default": True, "revision_checked": True,
                    "atomic_head": True, "outputs": "immutable per-run bundles",
                    "limits": ["trusted project adapter/scripts are not sandboxed", "external script side effects are outside bundle rollback"]}
        if operation == "discover":
            result, evidence = self.adapter("discover", None, request.get("options", {}), "discovery")
            return {**result, "evidence": evidence}
        if operation == "list":
            return {"ok": True, "documents": [{"document_id": p.stem, "revision": self.read(p.stem)["revision"]}
                                                for p in sorted(self.heads.glob("*.json"))]}
        identifier = request.get("document_id")
        self.path(identifier)
        with self.lock(identifier):
            before = self.read(identifier)
            if operation == "inspect":
                if before is None:
                    raise ControlError("document does not exist")
                return {"ok": True, "document_id": identifier, **before}
            expected = before["revision"] if before else None
            if operation == "create":
                if before:
                    raise ControlError("document already exists")
                after = request.get("recipe")
            else:
                if before is None:
                    raise ControlError("document does not exist")
                if request.get("if_revision") != expected:
                    raise ControlError("revision conflict; inspect before operating")
                if operation == "playtest":
                    return self.playtest(identifier, before, request)
                if operation == "patch":
                    after = apply_patch(before["recipe"], request.get("patch"))
                elif operation == "replace":
                    after = request.get("recipe")
                elif operation == "restore":
                    digest = request.get("restore_revision", "")
                    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                        raise ControlError("restore_revision requires SHA-256")
                    after = decode(self.contained(".arcont/history/" + identifier + "/" + digest + ".json").read_text(encoding="utf-8"))
                    if revision(after) != digest:
                        raise ControlError("corrupt history revision")
                else:
                    after = before["recipe"]
            self.validate(after, identifier)
            dry_run = request.get("dry_run", True)
            if not isinstance(dry_run, bool):
                raise ControlError("dry_run must be a boolean")
            result, evidence = self.adapter("run", after, request.get("options", {}), identifier)
            if not result.get("ok"):
                return {**result, "committed": False, "previous_revision": expected, "evidence": evidence}
            # Recheck dependencies and source after engine execution, not only before.
            self.validate(after, identifier)
            current = self.read(identifier)
            if (current["revision"] if current else None) != expected:
                raise ControlError("revision changed during engine execution")
            digest = revision(after)
            if not dry_run:
                if before:
                    atomic_write(self.contained(".arcont/history/" + identifier + "/" + expected + ".json"), before["recipe"])
                atomic_write(self.contained(".arcont/history/" + identifier + "/" + digest + ".json"), after)
                atomic_write(self.path(identifier), {"revision": digest, "recipe": after, "last_build": evidence})
            return {"ok": True, "document_id": identifier, "committed": not dry_run, "revision": digest,
                    "previous_revision": expected, "changed_paths": changes(before["recipe"] if before else None, after),
                    "recipe": after, "result": result, "evidence": evidence}

    def playtest(self, identifier, before, request):
        """Observe one accepted scene without publishing a source revision."""
        if request.get("dry_run", True) is not True:
            raise ControlError("playtest does not publish; dry_run must remain true")
        session = request.get("session")
        errors = validate_playtest(session)
        if errors: raise ControlError("invalid playtest session: " + "; ".join(errors))
        configuration = self.config.get("playtest", {})
        extension = configuration.get("script", "")
        if not isinstance(extension, str) or not extension.startswith("res://") or not extension.endswith(".gd"):
            raise ControlError("project has no configured playtest script")
        extension_path = self.contained(extension[6:])
        if not extension_path.is_file(): raise ControlError("playtest script missing")
        scene = request.get("scene")
        if not isinstance(scene, str) or not scene.endswith(".tscn"):
            raise ControlError("playtest requires a saved scene artifact path")
        build = before.get("last_build", {})
        directory = self.contained(build.get("directory", ""))
        if self.runs not in directory.parents: raise ControlError("accepted bundle is outside run directory")
        artifact = next((item for item in build.get("manifest", {}).get("artifacts", []) if item.get("path") == scene), None)
        source = directory / scene
        if not artifact or source.is_symlink() or directory not in source.resolve().parents or not source.is_file():
            raise ControlError("scene must be a recorded artifact in the accepted bundle")
        scene_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        if scene_hash != artifact.get("sha256"): raise ControlError("accepted scene bytes changed")
        self.validate(before["recipe"], identifier)
        options = request.get("options", {})
        if not isinstance(options, dict): raise ControlError("options requires an object")
        if any("capture" in command for command in session["commands"]) and options.get("render") is not True:
            raise ControlError("playtest camera captures require options.render=true")
        recipe = {"version": 1, "id": identifier, "dependencies": {
            str(source.relative_to(self.root)): scene_hash,
            str(extension_path.relative_to(self.root)): hashlib.sha256(extension_path.read_bytes()).hexdigest()},
            "steps": [
                {"op": "load", "id": "playtest_world", "path": str(source), "instantiate": True},
                {"op": "attach", "target": "playtest_world"},
                {"op": "script", "id": "playtest_session", "path": extension,
                 "args": {"world": "playtest_world", "session": session}}]}
        self.validate(recipe, identifier)
        result, evidence = self.adapter("run", recipe, options, identifier)
        self.validate(recipe, identifier)
        self.validate(before["recipe"], identifier)
        if self.read(identifier) != before: raise ControlError("document changed during playtest")
        report = next((step.get("value") for step in result.get("steps", []) if step.get("id") == "playtest_session"), None)
        if result.get("ok") and (not isinstance(report, dict) or not isinstance(report.get("passed"), bool)):
            raise ControlError("playtest adapter must return a boolean passed outcome")
        return {"ok": result.get("ok", False), "passed": report.get("passed", False) if isinstance(report, dict) else False,
                "committed": False, "document_id": identifier, "revision": before["revision"],
                "scene": scene, "source_scene_sha256": scene_hash, "session": session,
                "result": result, "report": report, "evidence": evidence,
                "limits": ["completed execution and passed expectations are distinct", "no cross-platform determinism or device FPS claim"]}


def respond(project, request):
    try:
        return {"protocol_version": 1, **Authoring(project).execute(request)}
    except (ControlError, ValueError, OSError, subprocess.SubprocessError) as exc:
        return {"protocol_version": 1, "ok": False, "committed": False, "error": str(exc)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--request", default="-")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        request = decode(sys.stdin.read() if args.request == "-" else Path(args.request).read_text(encoding="utf-8"))
        result = respond(args.project, request)
    except (ValueError, OSError) as exc:
        result = {"protocol_version": 1, "ok": False, "error": str(exc)}
    if args.output:
        atomic_write(Path(args.output), result)
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())

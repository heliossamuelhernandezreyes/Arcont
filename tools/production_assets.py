#!/usr/bin/env python3
"""Validate project-owned delivered assets and stage immutable dependency bundles.

Asset Vault remains the source catalogue. This consumes an already reviewed game
manifest; it does not infer licensing, download new art or claim Android approval.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile
from urllib.parse import unquote, urlsplit

try:
    from tools.license_policy import classify, ALIASES, POLICIES
    from tools.model_forge_inspect import inspect, load_gltf
except ModuleNotFoundError:
    from license_policy import classify, ALIASES, POLICIES
    from model_forge_inspect import inspect, load_gltf


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def local(root, relative):
    root = Path(root).resolve()
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise ValueError("expected a portable project-relative path")
    p = PurePosixPath(relative)
    if p.is_absolute() or ".." in p.parts or ":" in relative:
        raise ValueError("path must remain inside the project")
    candidate = root.joinpath(*p.parts)
    if any(part.is_symlink() for part in [candidate, *candidate.parents] if part != root.parent):
        raise ValueError("symlink paths are not accepted")
    resolved = candidate.resolve()
    if root not in resolved.parents:
        raise ValueError("path escapes project")
    return resolved


def closure(root, model):
    """External glTF buffers/images are copied with their original relative paths."""
    source = local(root, model)
    document = load_gltf(source)
    paths = {model}
    for resource in document.get("buffers", []) + document.get("images", []):
        uri = resource.get("uri")
        if not uri or uri.startswith("data:"):
            continue
        parsed = urlsplit(uri)
        if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
            raise ValueError("only local glTF dependencies are supported")
        relative = unquote(uri)
        if PurePosixPath(relative).is_absolute() or ".." in PurePosixPath(relative).parts:
            raise ValueError("glTF dependency escapes its directory")
        dependent = (PurePosixPath(model).parent / relative).as_posix()
        path = local(root, dependent)
        if not path.is_file():
            raise ValueError("missing glTF dependency: " + dependent)
        if "byteLength" in resource and path.stat().st_size < resource["byteLength"]:
            raise ValueError("truncated glTF buffer: " + dependent)
        paths.add(dependent)
    return sorted(paths)


def validate_plan(project, plan):
    if plan.get("version") != 1 or not re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", plan.get("id", "")):
        raise ValueError("invalid production asset plan identity")
    if not plan.get("assets"):
        raise ValueError("asset plan is empty")
    proof_path = local(project, plan["provenance_manifest"])
    if digest(proof_path) != plan["provenance_sha256"]:
        raise ValueError("provenance manifest changed")
    proof = json.loads(proof_path.read_text())
    delivered = {x["path"]: x["sha256"] for x in proof["delivered_files"]}
    sources = {x["name"]: x for x in proof["sources"]}
    ids = set()
    files = {}
    results = []
    for asset in plan["assets"]:
        identity = asset.get("id", "")
        if not re.fullmatch(r"[a-z][a-z0-9_.-]{0,95}", identity) or identity in ids:
            raise ValueError("invalid or duplicate semantic asset ID")
        ids.add(identity)
        source = sources[asset["source_name"]]
        license_name = source["license"]
        normalized = " ".join(license_name.lower().replace("_", " ").split())
        exact_policy = normalized in ALIASES or license_name.upper() in POLICIES
        policy = classify(license_name) if exact_policy else None
        if not policy or policy.tier != "green" or not source.get("url"):
            raise ValueError("asset lacks a reviewed GREEN source in the game manifest")
        path = local(project, asset["path"])
        if path.suffix.lower() not in {".gltf", ".glb"}:
            raise ValueError("asset must already be normalized glTF/GLB")
        dependencies = closure(project, asset["path"])
        document = load_gltf(path)
        accessors = document.get("accessors", [])
        for mesh in document.get("meshes", []):
            for primitive in mesh.get("primitives", []):
                if primitive.get("mode", 4) != 4:
                    raise ValueError("production budget requires triangle-list primitives")
                position = primitive.get("attributes", {}).get("POSITION")
                count_index = primitive.get("indices", position)
                for index in (position, count_index):
                    if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(accessors):
                        raise ValueError("invalid geometry accessor")
                    count = accessors[index].get("count")
                    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
                        raise ValueError("invalid geometry count")
                if accessors[count_index]["count"] % 3:
                    raise ValueError("incomplete triangle-list geometry")
        for relative in dependencies:
            file = local(project, relative)
            actual = digest(file)
            if delivered.get(relative) != actual:
                raise ValueError("unverified or changed delivered file: " + relative)
            files[relative] = {"sha256": actual, "size_bytes": file.stat().st_size}
        measured = inspect(path)
        budget = asset["budget"]
        for metric in ("triangles", "materials"):
            bound = budget[metric + "_max"]
            if isinstance(bound, bool) or not isinstance(bound, int) or bound < 1:
                raise ValueError("invalid asset budget")
            if measured[metric] > bound:
                raise ValueError(f"{identity}: {metric} exceeds its production profile")
        if measured["gltf_version"] != "2.0" or measured["meshes"] == 0:
            raise ValueError("invalid or empty glTF model")
        if measured["extensions_required"]:
            raise ValueError("required extensions need a separately tested processor")
        if asset.get("require_skin") and measured["skins"] == 0:
            raise ValueError("character has no skin")
        measured["path"] = asset["path"]
        results.append({"id": identity, "source": source, "inspection": measured,
                        "dependencies": dependencies, "budget": budget,
                        "engine_profile": asset.get("engine_profile", {})})
    return {"ok": True, "plan": plan["id"], "assets": results, "files": files,
            "provenance_sha256": plan["provenance_sha256"],
            "limits": ["game-reviewed source provenance; no fresh upstream license review",
                       "structural budget validation; runtime evidence still required"]}


def stage(project, plan, destination):
    project = Path(project).resolve()
    report = validate_plan(project, plan)
    canonical = json.dumps({"plan": plan, "files": report["files"]}, sort_keys=True, separators=(",", ":"))
    fingerprint = hashlib.sha256(canonical.encode()).hexdigest()
    parent = local(project, destination)
    parent.mkdir(parents=True, exist_ok=True)
    output = parent / (plan["id"] + "-" + fingerprint[:16])
    report["bundle_sha256"] = fingerprint
    report["bundle_directory"] = str(output.relative_to(project))
    manifest = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if output.exists():
        if output.is_symlink() or not (output / "bundle.json").is_file():
            raise ValueError("bundle destination is unmanaged")
        if (output / "bundle.json").read_text() != manifest:
            raise ValueError("bundle manifest was modified")
        for relative, metadata in report["files"].items():
            if digest(local(output, relative)) != metadata["sha256"]:
                raise ValueError("existing bundle was modified")
        return report
    temporary = Path(tempfile.mkdtemp(prefix=".candidate-", dir=parent))
    try:
        for relative, metadata in report["files"].items():
            src = local(project, relative)
            target = temporary / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, target)
            if digest(target) != metadata["sha256"] or digest(src) != metadata["sha256"]:
                raise ValueError("source changed during staging")
        if digest(local(project, plan["provenance_manifest"])) != plan["provenance_sha256"]:
            raise ValueError("provenance changed during staging")
        (temporary / "bundle.json").write_text(manifest)
        # rename never replaces a nonempty existing bundle; no source asset is changed.
        os.rename(temporary, output)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return report

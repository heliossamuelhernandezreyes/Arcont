#!/usr/bin/env python3
"""License-aware public asset discovery and staging for external projects.

V1 supports the Poly Haven public API through an explicit provider adapter.
Search/file discovery are read-only network operations. Staging is a bounded
external-project write that can only download a file URL returned by the live
provider manifest and bound by its canonical SHA-256.

No arbitrary URL fetch, scraping, archive extraction, or license inference is
exposed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

PROTOCOL_VERSION = 1
OPERATIONS = ("capabilities", "providers", "search", "files", "stage", "list")
PROVIDER = "polyhaven"
API_BASE = "https://api.polyhaven.com"
API_ASSETS = API_BASE + "/assets"
API_FILES = API_BASE + "/files/{asset_id}"
API_TERMS = "https://polyhaven.com/our-api"
LICENSE_URL = "https://polyhaven.com/license"
PROVIDER_SITE = "https://polyhaven.com"
USER_AGENT = "ARCONT-PublicAssetDiscovery/1.0 (+https://github.com/heliossamuelhernandezreyes/Arcont)"
MAX_JSON_BYTES = 64 * 1024 * 1024
MAX_DOWNLOAD_BYTES = 256 * 1024 * 1024
MAX_RECORD_BYTES = 1024 * 1024
MAX_RECORDS = 2000
MAX_RESULTS = 50
ASSET_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,199}$")
SEMANTIC_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
ALLOWED_DOWNLOAD_HOSTS = {"dl.polyhaven.org"}
STAGE_EXTENSIONS = {
    ".glb",
    ".hdr", ".exr", ".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff",
}
TYPE_QUERY = {
    "all": None,
    "models": "models",
    "textures": "textures",
    "hdris": "hdris",
}
TYPE_NAMES = {0: "hdri", 1: "texture", 2: "model"}


def _canonical_sha(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _fetch_json(url: str, timeout: int = 30) -> Any:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        declared = response.headers.get("Content-Length")
        if declared:
            try:
                declared_size = int(declared)
            except ValueError:
                declared_size = None
            if declared_size is not None and declared_size > MAX_JSON_BYTES:
                raise ValueError("provider JSON response exceeds size limit")
        body = response.read(MAX_JSON_BYTES + 1)
        if len(body) > MAX_JSON_BYTES:
            raise ValueError("provider JSON response exceeds size limit")
    value = json.loads(body.decode("utf-8"))
    return value


def _provider_info() -> dict[str, Any]:
    return {
        "id": PROVIDER,
        "name": "Poly Haven",
        "site": PROVIDER_SITE,
        "api": API_BASE,
        "api_terms": API_TERMS,
        "asset_license": "CC0",
        "license_url": LICENSE_URL,
        "commercial_use": True,
        "asset_attribution_required": False,
        "api_attribution_required": True,
        "api_credit": "Poly Haven",
        "api_user_agent_required": True,
        "network_mode": "official-public-api-only",
        "scraping_allowed_by_arcont_adapter": False,
    }


def _project_policy(project: Path) -> dict[str, Any]:
    path = project / "project.intent.json"
    if not path.is_file():
        raise ValueError("project.intent.json is required for public asset operations")
    try:
        from tools.arcont_bridge import validate_intent
    except ModuleNotFoundError:
        from arcont_bridge import validate_intent
    intent = validate_intent(json.loads(path.read_text(encoding="utf-8")))
    policy = intent.get("asset_policy", {})
    if policy.get("public_assets") is not True:
        raise PermissionError("project intent does not allow public assets")
    if policy.get("allow_network_discovery") is not True:
        raise PermissionError("project intent does not allow network asset discovery")
    allowed = policy.get("allowed_licenses")
    if isinstance(allowed, list) and "CC0" not in allowed:
        raise PermissionError("project allowed_licenses does not permit Poly Haven CC0 assets")
    forbidden = policy.get("forbidden_licenses")
    if isinstance(forbidden, list) and "CC0" in forbidden:
        raise PermissionError("project forbidden_licenses blocks Poly Haven CC0 assets")
    return policy


def _asset_type(meta: dict[str, Any]) -> str:
    return TYPE_NAMES.get(meta.get("type"), "unknown")


def _search_text(asset_id: str, meta: dict[str, Any]) -> str:
    pieces = [
        asset_id,
        str(meta.get("name", "")),
        str(meta.get("description", "")),
        str(meta.get("category", "")),
    ]
    tags = meta.get("tags")
    if isinstance(tags, list):
        pieces.extend(str(tag) for tag in tags)
    return " ".join(pieces).lower()


def _score(query: str, asset_id: str, meta: dict[str, Any]) -> tuple[int, int, str]:
    q = query.strip().lower()
    if not q:
        return (0, int(meta.get("download_count") or 0), asset_id)
    name = str(meta.get("name", "")).lower()
    aid = asset_id.lower()
    tags = [str(v).lower() for v in meta.get("tags", []) if isinstance(v, str)]
    haystack = _search_text(asset_id, meta)
    score = 0
    if q == aid:
        score += 1000
    if q == name:
        score += 900
    if q in aid:
        score += 500
    if q in name:
        score += 450
    if q in tags:
        score += 350
    words = [word for word in re.split(r"\s+", q) if word]
    score += sum(25 for word in words if word in haystack)
    return (score, int(meta.get("download_count") or 0), asset_id)


def search(project: Path, query: Any, asset_type: Any = "all", limit: Any = 10) -> dict[str, Any]:
    _project_policy(project)
    if not isinstance(query, str) or len(query) > 500:
        raise ValueError("search query must be a string <=500 chars")
    if asset_type not in TYPE_QUERY:
        raise ValueError(f"asset_type must be one of {sorted(TYPE_QUERY)}")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_RESULTS:
        raise ValueError(f"limit must be in [1,{MAX_RESULTS}]")
    params = {}
    provider_type = TYPE_QUERY[asset_type]
    if provider_type:
        params["type"] = provider_type
    url = API_ASSETS + (("?" + urllib.parse.urlencode(params)) if params else "")
    payload = _fetch_json(url)
    if not isinstance(payload, dict):
        raise ValueError("provider assets response must be an object")

    scored: list[tuple[tuple[int, int, str], str, dict[str, Any]]] = []
    for asset_id, meta in payload.items():
        if not isinstance(asset_id, str) or not isinstance(meta, dict):
            continue
        rank = _score(query, asset_id, meta)
        if query.strip() and rank[0] <= 0:
            continue
        scored.append((rank, asset_id, meta))
    scored.sort(key=lambda row: (-row[0][0], -row[0][1], row[0][2]))
    rows = []
    for rank, asset_id, meta in scored[:limit]:
        rows.append({
            "provider": PROVIDER,
            "provider_asset_id": asset_id,
            "name": meta.get("name"),
            "asset_type": _asset_type(meta),
            "category": meta.get("category"),
            "tags": meta.get("tags") if isinstance(meta.get("tags"), list) else [],
            "authors": meta.get("authors") if isinstance(meta.get("authors"), dict) else {},
            "polycount": meta.get("polycount"),
            "download_count": meta.get("download_count"),
            "files_hash": meta.get("files_hash"),
            "thumbnail_url": meta.get("thumbnail_url"),
            "asset_license": "CC0",
            "commercial_use": True,
            "asset_attribution_required": False,
            "api_attribution_required": True,
            "provider_credit": "Poly Haven",
            "source_api": url,
            "match_score": rank[0],
        })
    return {
        "ok": True,
        "write_performed": False,
        "result": {
            "provider": _provider_info(),
            "query": query,
            "asset_type": asset_type,
            "count": len(rows),
            "results": rows,
            "catalog_response_sha256": _canonical_sha(payload),
        },
    }


def _flatten_files(value: Any, path: tuple[str, ...] = ()) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if isinstance(value, dict):
        url = value.get("url")
        if isinstance(url, str):
            parsed = urllib.parse.urlparse(url)
            decoded_path = urllib.parse.unquote(parsed.path)
            extension = Path(decoded_path).suffix.lower()
            dependencies = value.get("include")
            has_dependencies = isinstance(dependencies, (dict, list)) and bool(dependencies)
            rows.append({
                "file_key": "/".join(path),
                "url": url,
                "host": parsed.hostname,
                "extension": extension,
                "size": value.get("size"),
                "md5": value.get("md5"),
                "has_external_dependencies": has_dependencies,
                "download_host_allowed": parsed.scheme == "https" and parsed.hostname in ALLOWED_DOWNLOAD_HOSTS,
                "stage_extension_allowed": extension in STAGE_EXTENSIONS and not has_dependencies,
            })
        for key, child in value.items():
            if key == "url":
                continue
            if isinstance(child, (dict, list)):
                rows.extend(_flatten_files(child, (*path, str(key))))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            rows.extend(_flatten_files(child, (*path, str(index))))
    return rows


def files(project: Path, asset_id: Any) -> dict[str, Any]:
    _project_policy(project)
    if not isinstance(asset_id, str) or not ASSET_ID.fullmatch(asset_id):
        raise ValueError("invalid provider asset id")
    url = API_FILES.format(asset_id=urllib.parse.quote(asset_id, safe=""))
    payload = _fetch_json(url)
    if not isinstance(payload, dict):
        raise ValueError("provider files response must be an object")
    manifest_sha = _canonical_sha(payload)
    rows = sorted(_flatten_files(payload), key=lambda row: row["file_key"])
    return {
        "ok": True,
        "write_performed": False,
        "result": {
            "provider": _provider_info(),
            "provider_asset_id": asset_id,
            "source_api": url,
            "manifest_sha256": manifest_sha,
            "file_count": len(rows),
            "files": rows,
        },
    }


def _reject_symlink_ancestors(project: Path, path: Path) -> None:
    root = project.resolve()
    lexical = path if path.is_absolute() else root / path
    try:
        rel = lexical.relative_to(root)
    except ValueError as exc:
        raise ValueError("path escapes external project") from exc
    current = root
    for part in rel.parts:
        current = current / part
        if current.exists() and current.is_symlink():
            raise ValueError("symlink paths are not accepted")


def _safe_destination(project: Path, relative: str) -> Path:
    root = project.resolve()
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError("safe project-relative destination required")
    lexical = root / rel
    _reject_symlink_ancestors(root, lexical)
    parent = lexical.parent.resolve()
    if parent != root and root not in parent.parents:
        raise ValueError("destination escapes external project")
    return lexical


class _AllowlistedRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urllib.parse.urlparse(newurl)
        if parsed.scheme != "https" or parsed.hostname not in ALLOWED_DOWNLOAD_HOSTS:
            raise urllib.error.HTTPError(
                newurl,
                code,
                "provider redirect target is outside download host allowlist",
                headers,
                fp,
            )
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _download_opener():
    return urllib.request.build_opener(_AllowlistedRedirectHandler())


def _download(url: str, target: Path, expected_size: Any, expected_md5: Any) -> dict[str, Any]:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_DOWNLOAD_HOSTS:
        raise ValueError("download URL is outside provider host allowlist")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT}, method="GET")
    sha = hashlib.sha256()
    md5 = hashlib.md5(usedforsecurity=False)
    total = 0
    opener = _download_opener()
    with opener.open(request, timeout=60) as response, target.open("wb") as handle:
        final_url = response.geturl()
        final_parsed = urllib.parse.urlparse(final_url)
        if final_parsed.scheme != "https" or final_parsed.hostname not in ALLOWED_DOWNLOAD_HOSTS:
            raise ValueError("provider download redirected outside host allowlist")
        declared = response.headers.get("Content-Length")
        if declared:
            try:
                declared_size = int(declared)
            except ValueError:
                declared_size = None
            if declared_size is not None and declared_size > MAX_DOWNLOAD_BYTES:
                raise ValueError("download exceeds v1 size limit")
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_DOWNLOAD_BYTES:
                raise ValueError("download exceeds v1 size limit")
            sha.update(chunk)
            md5.update(chunk)
            handle.write(chunk)
    if isinstance(expected_size, int) and expected_size >= 0 and total != expected_size:
        raise ValueError(f"download size mismatch: {total} != {expected_size}")
    digest_md5 = md5.hexdigest()
    if isinstance(expected_md5, str) and expected_md5 and digest_md5.lower() != expected_md5.lower():
        raise ValueError("download MD5 does not match provider manifest")
    return {"bytes": total, "sha256": sha.hexdigest(), "md5": digest_md5}


def _record_dir(project: Path) -> Path:
    return _safe_destination(project, ".arcont/assets/public")


def list_records(project: Path) -> dict[str, Any]:
    root = project.resolve()
    base = _record_dir(root)
    records = []
    if not base.exists():
        return {"ok": True, "write_performed": False, "result": {"assets": [], "count": 0}}
    _reject_symlink_ancestors(root, base)
    if not base.is_dir():
        raise ValueError("public asset provenance path is not a directory")
    paths = sorted(base.glob("*.asset.json"))
    if len(paths) > MAX_RECORDS:
        raise ValueError("public asset provenance record count exceeds v1 limit")
    for path in paths:
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"invalid public asset provenance entry: {path.name}")
        if path.stat().st_size > MAX_RECORD_BYTES:
            raise ValueError(f"public asset provenance record exceeds size limit: {path.name}")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid public asset provenance record: {path.name}") from exc
        if not isinstance(data, dict):
            raise ValueError(f"public asset provenance record must be an object: {path.name}")
        records.append(data)
    return {"ok": True, "write_performed": False, "result": {"assets": records, "count": len(records)}}


def _recover_completed_stage(project: Path, destination: Path, record_path: Path, semantic_id: str) -> dict[str, Any] | None:
    internal = destination / ".arcont-stage-record.json"
    if not destination.is_dir() or record_path.exists() or not internal.is_file() or internal.is_symlink():
        return None
    if internal.stat().st_size > MAX_RECORD_BYTES:
        raise ValueError("recoverable stage record exceeds size limit")
    record = json.loads(internal.read_text(encoding="utf-8"))
    if not isinstance(record, dict) or record.get("id") != semantic_id:
        raise ValueError("staged destination exists without matching recoverable provenance")
    staged = project / record.get("staged_path", "")
    staged = staged.resolve()
    root = project.resolve()
    if staged == root or root not in staged.parents or not staged.is_file():
        raise ValueError("recoverable staged asset path is invalid")
    digest = hashlib.sha256()
    total = 0
    with staged.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            total += len(chunk)
            digest.update(chunk)
    if digest.hexdigest() != record.get("sha256") or total != record.get("bytes"):
        raise ValueError("recoverable staged asset no longer matches provenance")
    record_path.parent.mkdir(parents=True, exist_ok=True)
    _reject_symlink_ancestors(root, record_path.parent)
    tmp_record = record_path.with_suffix(record_path.suffix + ".tmp")
    tmp_record.write_text(json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + chr(10), encoding="utf-8")
    os.replace(tmp_record, record_path)
    return record


def stage(project: Path, request: dict[str, Any]) -> dict[str, Any]:
    root = project.resolve()
    _project_policy(root)
    semantic_id = request.get("semantic_id")
    asset_id = request.get("asset_id")
    file_key = request.get("file_key")
    expected_manifest = request.get("manifest_sha256")
    if not isinstance(semantic_id, str) or not SEMANTIC_ID.fullmatch(semantic_id):
        raise ValueError("stage requires safe semantic_id")
    if not isinstance(asset_id, str) or not ASSET_ID.fullmatch(asset_id):
        raise ValueError("stage requires valid provider asset id")
    if not isinstance(file_key, str) or not file_key or len(file_key) > 1000:
        raise ValueError("stage requires bounded file_key")
    if not isinstance(expected_manifest, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_manifest):
        raise ValueError("stage requires manifest_sha256 from asset.public.files")

    destination_parent = _safe_destination(root, "assets/public/polyhaven")
    destination = _safe_destination(root, f"assets/public/polyhaven/{semantic_id}")
    record_path = _safe_destination(root, f".arcont/assets/public/{semantic_id}.asset.json")
    _reject_symlink_ancestors(root, destination_parent)
    _reject_symlink_ancestors(root, destination)
    _reject_symlink_ancestors(root, record_path)

    recovered = _recover_completed_stage(root, destination, record_path, semantic_id)
    if recovered is not None:
        return {"ok": True, "write_performed": True, "result": recovered, "recovered": True}
    if destination.exists() or record_path.exists():
        raise ValueError("semantic_id is already staged")

    manifest_report = files(root, asset_id)
    manifest = manifest_report["result"]
    if manifest["manifest_sha256"] != expected_manifest:
        raise ValueError("provider files manifest changed since selection; rediscover before staging")
    matches = [row for row in manifest["files"] if row["file_key"] == file_key]
    if len(matches) != 1:
        raise ValueError("file_key does not select exactly one provider file")
    selected = matches[0]
    if not selected["download_host_allowed"]:
        raise ValueError("selected provider file uses a non-allowlisted host")
    if not selected["stage_extension_allowed"]:
        raise ValueError("selected provider file extension/dependency policy is not stageable in v1")
    if isinstance(selected.get("size"), int) and selected["size"] > MAX_DOWNLOAD_BYTES:
        raise ValueError("selected provider file exceeds v1 size limit")

    destination_parent.mkdir(parents=True, exist_ok=True)
    _reject_symlink_ancestors(root, destination_parent)
    staging = Path(tempfile.mkdtemp(prefix=f".{semantic_id}.arcont-public-", dir=destination_parent))
    try:
        parsed = urllib.parse.urlparse(selected["url"])
        filename = Path(urllib.parse.unquote(parsed.path)).name
        if not filename or Path(filename).suffix.lower() not in STAGE_EXTENSIONS:
            raise ValueError("provider URL has no safe stageable filename")
        target = staging / filename
        integrity = _download(
            selected["url"], target, selected.get("size"), selected.get("md5")
        )
        final_target = destination / filename
        record = {
            "protocol": "arcont-public-asset",
            "version": 1,
            "id": semantic_id,
            "origin": "public-provider",
            "provider": "Poly Haven",
            "provider_id": PROVIDER,
            "provider_asset_id": asset_id,
            "provider_file_key": file_key,
            "source_api": manifest["source_api"],
            "download_url": selected["url"],
            "staged_path": final_target.relative_to(root).as_posix(),
            "extension": final_target.suffix.lower(),
            "bytes": integrity["bytes"],
            "sha256": integrity["sha256"],
            "upstream_md5": selected.get("md5"),
            "verified_md5": integrity["md5"],
            "files_manifest_sha256": expected_manifest,
            "asset_license": "CC0",
            "license_url": LICENSE_URL,
            "commercial_use": True,
            "asset_attribution_required": False,
            "api_attribution_required": True,
            "provider_credit": "Poly Haven",
            "api_terms": API_TERMS,
            "provenance_status": "provider-api-and-download-integrity-verified",
            "network_access": True,
            "archive_extracted": False,
        }
        (staging / ".arcont-stage-record.json").write_text(
            json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + chr(10),
            encoding="utf-8",
        )
        os.replace(staging, destination)

        record_path.parent.mkdir(parents=True, exist_ok=True)
        _reject_symlink_ancestors(root, record_path.parent)
        temp_record = record_path.with_suffix(record_path.suffix + ".tmp")
        temp_record.write_text(
            json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + chr(10),
            encoding="utf-8",
        )
        os.replace(temp_record, record_path)
        internal_record = destination / ".arcont-stage-record.json"
        if internal_record.is_file() and not internal_record.is_symlink():
            internal_record.unlink()
    except Exception:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        raise
    return {"ok": True, "write_performed": True, "result": record, "recovered": False}


def execute(project: Path, request: dict[str, Any]) -> dict[str, Any]:
    if request.get("protocol_version") != PROTOCOL_VERSION:
        raise ValueError("request requires protocol_version=1")
    operation = request.get("operation")
    if operation not in OPERATIONS:
        raise ValueError(f"unsupported operation: {operation}")
    root = Path(project).resolve()
    if not root.is_dir():
        raise ValueError("external project root must exist")

    if operation == "capabilities":
        return {
            "ok": True,
            "write_performed": False,
            "operations": list(OPERATIONS),
            "providers": [_provider_info()],
            "mutating_operations": ["stage"],
            "arbitrary_url_download": False,
            "archive_extraction": False,
            "dependency_policy": "single-file-self-contained",
            "stageable_extensions": sorted(STAGE_EXTENSIONS),
            "max_download_bytes": MAX_DOWNLOAD_BYTES,
            "max_record_bytes": MAX_RECORD_BYTES,
            "max_records": MAX_RECORDS,
        }
    if operation == "providers":
        return {"ok": True, "write_performed": False, "result": {"providers": [_provider_info()]}}
    if operation == "search":
        return search(root, request.get("query", ""), request.get("asset_type", "all"), request.get("limit", 10))
    if operation == "files":
        return files(root, request.get("asset_id"))
    if operation == "list":
        return list_records(root)
    if operation == "stage":
        return stage(root, request)
    raise AssertionError("unreachable")


def respond(project: Path, request: Any) -> dict[str, Any]:
    try:
        if not isinstance(request, dict):
            raise ValueError("request must be an object")
        return {"protocol_version": PROTOCOL_VERSION, **execute(project, request)}
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        PermissionError,
        json.JSONDecodeError,
        urllib.error.URLError,
    ) as exc:
        return {
            "protocol_version": PROTOCOL_VERSION,
            "ok": False,
            "write_performed": False,
            "error": str(exc),
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--request", default="-")
    args = parser.parse_args()
    try:
        raw = sys.stdin.read() if args.request == "-" else Path(args.request).read_text(encoding="utf-8")
        result = respond(Path(args.project), json.loads(raw))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"protocol_version": 1, "ok": False, "write_performed": False, "error": str(exc)}
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())

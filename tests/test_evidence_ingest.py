import argparse
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("evidence_ingest", ROOT / "tools" / "evidence_ingest.py")
mod = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(mod)


def args(provider, **overrides):
    base = dict(
        provider=provider,
        claim_ref=None,
        provider_version=None,
        provider_commit=None,
        source_ref=None,
        build_type=None,
        maturity_ceiling="L1_SOURCE_TRACED",
    )
    base.update(overrides)
    return argparse.Namespace(**base)


class EvidenceIngestTests(unittest.TestCase):
    def test_godot_benchmarks_real_shape(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "results.json"
            p.write_text(json.dumps({
                "engine": {"version": "v4.7.2.stable.official", "version_hash": "e" * 40},
                "system": {"os": "Linux", "cpu_name": "CPU", "cpu_architecture": "x86_64", "cpu_count": 4},
                "benchmarks": [{
                    "category": "SceneTree",
                    "name": "Process Nodes",
                    "results": {"render_cpu": 1.25, "idle": 0.4, "ignored": 99},
                }],
            }), encoding="utf-8")
            records = mod.adapt_godot_benchmarks(p, args("godot-benchmarks", provider_commit="a" * 40))
            self.assertEqual(len(records), 2)
            self.assertEqual({r["metric"]["normalized_name"] for r in records}, {"render_cpu_ms", "cpu_process_ms"})
            self.assertTrue(all(r["provenance"]["raw_sha256"] == mod.sha256(p) for r in records))

    def test_godot_benchmarks_prefixed_results(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "results.json"
            p.write_text(json.dumps({
                "engine": {"version": "v4.7.2.stable.official", "version_hash": "e" * 40},
                "system": {"os": "Linux"},
                "benchmarks": [{"category": "Render", "name": "X", "results": {"mesa": {"render_gpu": 2.0}}}],
            }), encoding="utf-8")
            records = mod.adapt_godot_benchmarks(p, args("godot-benchmarks"))
            self.assertEqual(records[0]["metric"]["normalized_name"], "render_gpu_ms")

    def test_runtime_lab_uses_canonical_raw_hash(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "run.result.json"
            p.write_text(json.dumps({
                "schema_version": 1,
                "benchmark_id": "ARC-BENCH-X",
                "run_id": "run-1",
                "engine": {"name": "godot", "version": "4.7.2-stable", "commit": "e" * 40},
                "platform": {"os": "Linux", "device": "VM", "cpu": "CPU", "gpu": "headless"},
                "runtime": {"build_type": "debug"},
                "experiment": {"hypothesis_ref": "ARC-HYP-X"},
                "metrics": {"cpu_ms": {"mean": 0.5}, "memory_mb": {"mean": 20.0}},
                "provenance": {"harness_commit": "a" * 40, "raw_data_sha256": "b" * 64},
                "aborted": False,
            }), encoding="utf-8")
            records = mod.adapt_runtime_lab(p, args("runtime-lab"))
            self.assertEqual(len(records), 2)
            self.assertTrue(all(r["claim_ref"] == "ARC-HYP-X" for r in records))
            self.assertTrue(all(r["provenance"]["raw_sha256"] == "b" * 64 for r in records))

    def test_trace_requires_existing_raw_and_matching_hash(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            raw = root / "trace.bin"
            raw.write_bytes(b"trace")
            extract = root / "extract.json"
            extract.write_text(json.dumps({
                "provider": "perfetto",
                "raw_trace_path": "trace.bin",
                "raw_sha256": mod.sha256(raw),
                "engine": {"version": "4.7.2-stable", "commit": "e" * 40},
                "system": {"platform": "Android", "hardware": "phone", "build_type": "release"},
                "metrics": [{"name": "sched_slice_ms", "unit": "ms", "normalized_name": "thread_cpu_slice_ms", "value": 1.5, "query": "sql"}],
                "limitations": ["synthetic test"],
            }), encoding="utf-8")
            records = mod.adapt_trace_extract(extract, args("perfetto"))
            self.assertEqual(records[0]["metric"]["normalized_name"], "thread_cpu_slice_ms")
            self.assertEqual(records[0]["provenance"]["raw_sha256"], mod.sha256(raw))

    def test_trace_hash_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "trace.bin").write_bytes(b"trace")
            extract = root / "extract.json"
            extract.write_text(json.dumps({
                "provider": "tracy",
                "raw_trace_path": "trace.bin",
                "raw_sha256": "0" * 64,
                "metrics": [{"name": "zone_ms", "unit": "ms", "value": 1.0}],
            }), encoding="utf-8")
            with self.assertRaises(ValueError):
                mod.adapt_trace_extract(extract, args("tracy"))

    def test_bundle_never_auto_promotes_or_assumes_equivalence(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "raw.json"
            p.write_text("{}", encoding="utf-8")
            r = mod.record(
                evidence_id="E", claim_ref=None, provider="godot-benchmarks", provider_version=None,
                provider_commit=None, repository="godotengine/godot-benchmarks", immutable_ref=None,
                source_path=str(p), engine_version=None, engine_commit=None, original_name="time",
                original_unit="ms", normalized_name="wall_time_ms", normalized_unit="ms", value=1.0,
                platform=None, hardware=None, build_type=None, raw_hash=mod.sha256(p),
                limitations=["test"], maturity_ceiling="L1_SOURCE_TRACED")
            b = mod.bundle("godot-benchmarks", p, [r])
            self.assertFalse(b["auto_promotion_allowed"])
            self.assertFalse(b["semantic_equivalence_assumed"])


if __name__ == "__main__":
    unittest.main()

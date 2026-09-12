import copy
import unittest

from tools.runtime_evidence import (
    CANONICAL_COMMIT,
    CANONICAL_VERSION,
    canonical_plan,
    load_json,
    repo_root,
    runner_manifest,
    validate_against_plan,
    validate_plan,
)


class RuntimeEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = repo_root()
        cls.plan = load_json(canonical_plan(cls.root))

    def valid_result(self, benchmark_id="ARC-BENCH-BASELINE-EMPTY-001"):
        bench = next(b for b in self.plan["benchmarks"] if b["id"] == benchmark_id)
        return {
            "schema_version": 1,
            "benchmark_id": benchmark_id,
            "run_id": "run-device-a-001",
            "engine": {"name": "godot", "version": CANONICAL_VERSION, "commit": CANONICAL_COMMIT},
            "platform": {"os": "Android 16", "device": "test-device", "cpu": "test-cpu", "gpu": "test-gpu"},
            "runtime": {"renderer": "mobile", "resolution": "1920x1080", "build_type": "release", "vsync": False},
            "experiment": {
                "campaign_id": self.plan["campaign_id"],
                "hypothesis_ref": bench["hypothesis_ref"],
                "variable": bench["variable"],
                "value": bench["sweep"][0],
                "repetition": 1,
                "warmup_seconds": bench["warmup_seconds"],
                "sample_seconds": bench["sample_seconds"],
                "controls": copy.deepcopy(bench.get("controls", {})),
            },
            "metrics": {metric: {"mean": 1.0} for metric in bench["metrics"]},
            "provenance": {"harness_commit": "1" * 40, "raw_data_sha256": "a" * 64},
            "aborted": False,
            "abort_reason": None,
        }

    def test_canonical_plan_passes(self):
        self.assertEqual(validate_plan(self.plan, self.root), [])

    def test_runner_manifest_requires_raw_provenance(self):
        manifest = runner_manifest(self.plan, "ARC-BENCH-SCENETREE-INACTIVE-NODE-001")
        req = manifest["runner_requirements"]
        self.assertTrue(req["raw_samples_required"])
        self.assertTrue(req["raw_data_sha256_required"])
        self.assertTrue(req["harness_commit_required"])
        self.assertTrue(req["record_experiment_controls"])
        self.assertFalse(req["interpretation_in_runner"])

    def test_valid_result_passes_campaign_contract(self):
        self.assertEqual(validate_against_plan(self.valid_result(), self.plan), [])

    def test_unknown_benchmark_is_rejected(self):
        result = self.valid_result()
        result["benchmark_id"] = "ARC-BENCH-NOT-REGISTERED"
        self.assertTrue(any("not registered" in e for e in validate_against_plan(result, self.plan)))

    def test_engine_drift_is_rejected(self):
        result = self.valid_result()
        result["engine"]["version"] = "future-version"
        self.assertTrue(any("engine identity" in e for e in validate_against_plan(result, self.plan)))

    def test_campaign_drift_is_rejected(self):
        result = self.valid_result()
        result["experiment"]["campaign_id"] = "ARC-CAMPAIGN-WRONG"
        self.assertTrue(any("campaign_id" in e for e in validate_against_plan(result, self.plan)))

    def test_unplanned_sweep_value_is_rejected(self):
        result = self.valid_result("ARC-BENCH-SCENETREE-INACTIVE-NODE-001")
        result["experiment"]["value"] = 777
        self.assertTrue(any("outside benchmark sweep" in e for e in validate_against_plan(result, self.plan)))

    def test_control_drift_is_rejected(self):
        result = self.valid_result("ARC-BENCH-SCENETREE-INACTIVE-NODE-001")
        result["experiment"]["controls"]["script_attached"] = True
        self.assertTrue(any("experiment.controls" in e for e in validate_against_plan(result, self.plan)))

    def test_missing_controls_are_rejected(self):
        result = self.valid_result("ARC-BENCH-SCENETREE-INACTIVE-NODE-001")
        result["experiment"].pop("controls")
        self.assertTrue(any("experiment.controls" in e for e in validate_against_plan(result, self.plan)))

    def test_incomplete_metric_is_rejected(self):
        result = self.valid_result("ARC-BENCH-SCENETREE-INACTIVE-NODE-001")
        result["metrics"]["cpu_ms"] = {"value": None, "status": "not-instrumented-yet"}
        self.assertTrue(any("complete numeric measurement" in e for e in validate_against_plan(result, self.plan)))

    def test_missing_raw_hash_is_rejected_for_completed_run(self):
        result = self.valid_result()
        result["provenance"].pop("raw_data_sha256")
        self.assertTrue(any("raw_data_sha256" in e for e in validate_against_plan(result, self.plan)))

    def test_aborted_run_may_omit_metrics_but_needs_reason(self):
        result = self.valid_result()
        result["aborted"] = True
        result["abort_reason"] = "thermal_limit"
        result["metrics"] = {}
        result["provenance"] = {}
        errors = validate_against_plan(result, self.plan)
        self.assertFalse(any("planned metric" in e for e in errors))
        self.assertFalse(any("harness_commit required" in e for e in errors))

    def test_plan_duplicate_id_is_rejected(self):
        plan = copy.deepcopy(self.plan)
        plan["benchmarks"].append(copy.deepcopy(plan["benchmarks"][0]))
        self.assertTrue(any("duplicate benchmark id" in e for e in validate_plan(plan, self.root)))


if __name__ == "__main__":
    unittest.main()

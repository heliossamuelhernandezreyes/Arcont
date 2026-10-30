"""Check local 2D capability evidence without promoting runtime maturity."""
import ast
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
FEATURES = {
    "normalization_tool": ("tools/png_sprite_normalize.py", "tests/test_png_sprite_normalize.py", "deterministic_normalization_implemented_tested"),
    "alpha_bounds_and_baseline_drift_checks": ("tools/png_sprite_audit.py", "tests/test_png_sprite_audit.py", "alpha_bounds_and_baseline_drift_checks_implemented_tested"),
}


def validate(root=ROOT):
    root = Path(root)
    matrix = root / "docs/knowledge/GODOT_2D_CAPABILITY_MATRIX.yaml"
    text = matrix.read_text(encoding="utf-8")
    match = re.search(r"(?ms)^  sprite_pipeline:\n(.*?)(?=^  [a-z][a-z0-9_]*:|\Z)", text)
    if match is None:
        return {"ok": False, "errors": ["sprite_pipeline matrix section missing"]}
    section = match.group(1)
    errors, evidence = [], []
    for missing_name, (implementation, test_file, claim) in FEATURES.items():
        paths = [root / implementation, root / test_file]
        if not all(p.is_file() for p in paths):
            errors.append("missing implementation or tests: " + missing_name)
            continue
        tree = ast.parse(paths[1].read_text())
        if not any(isinstance(n, ast.FunctionDef) and n.name.startswith("test_") for n in ast.walk(tree)):
            errors.append("no test definitions: " + test_file)
        for token in (implementation, test_file, claim):
            if token not in section:
                errors.append("matrix lacks local evidence: " + token)
        if re.search(r"(?m)^\s+- " + re.escape(missing_name) + r"\s*$", section):
            errors.append("implemented feature still listed as missing: " + missing_name)
        evidence.append({"feature": missing_name, "implementation": implementation, "tests": test_file,
            "implementation_sha256": hashlib.sha256(paths[0].read_bytes()).hexdigest(),
            "tests_sha256": hashlib.sha256(paths[1].read_bytes()).hexdigest()})
    return {"ok": not errors, "errors": errors, "evidence": evidence,
            "scope": "local files and test definitions; execution and external runtime evidence are not inferred"}


if __name__ == "__main__":
    result = validate()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["ok"] else 1)

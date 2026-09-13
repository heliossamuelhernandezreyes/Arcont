import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "map_forge_contract.py"
spec = importlib.util.spec_from_file_location("map_forge_contract", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def test_example_contract_is_valid():
    path = ROOT / "templates" / "map-forge" / "map_contract.example.json"
    assert module.validate_path(path) == []


def test_duplicate_ids_are_rejected():
    data = {
        "version": 1,
        "id": "bad",
        "bounds": {"width": 10, "depth": 10},
        "anchors": [
            {"id": "same", "kind": "spawn", "position": [0, 0, 0]},
            {"id": "same", "kind": "objective", "position": [1, 0, 0]},
        ],
        "routes": [],
        "regions": [],
        "authoring": {},
    }
    assert any("duplicate semantic id" in error for error in module.validate_contract(data))


def test_bad_route_is_rejected():
    data = {
        "version": 1,
        "id": "bad_route",
        "bounds": {"width": 10, "depth": 10},
        "anchors": [],
        "routes": [{"id": "route", "kind": "primary", "width": 0, "points": [[0, 0, 0]]}],
        "regions": [],
        "authoring": {},
    }
    errors = module.validate_contract(data)
    assert any("width must be positive" in error for error in errors)
    assert any("at least two valid" in error for error in errors)

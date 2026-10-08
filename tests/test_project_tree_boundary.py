import unittest
from pathlib import Path

from tools.arcont_agent import invoke_capability, repo_root
from tools.arcont_bridge import BridgeError, _safe_project
from tools.development_session import SessionError, _project


class ProjectTreeBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.root = repo_root().resolve()
        self.parent = self.root.parent
        self.inside = self.root / "docs"

    def test_bridge_rejects_arcont_itself(self):
        with self.assertRaises(BridgeError):
            _safe_project(self.root, self.root)

    def test_bridge_rejects_project_inside_arcont(self):
        with self.assertRaises(BridgeError):
            _safe_project(self.inside, self.root)

    def test_bridge_rejects_project_that_contains_arcont(self):
        with self.assertRaises(BridgeError):
            _safe_project(self.parent, self.root)

    def test_development_session_rejects_project_that_contains_arcont(self):
        with self.assertRaises(SessionError):
            _project(self.parent)

    def test_writer_control_plane_rejects_project_that_contains_arcont_before_spawn(self):
        with self.assertRaises(ValueError):
            invoke_capability(
                self.root,
                "godot.structured.control",
                self.parent,
                {"protocol_version": 1, "operation": "validate"},
                True,
                1,
            )


if __name__ == "__main__":
    unittest.main()

import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "sprite_pipeline", ROOT / "tools" / "sprite_pipeline.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class SpritePipelineTests(unittest.TestCase):
    def test_ordered_frames_preserves_state_and_frame_order(self):
        manifest = {
            "states": {
                "idle": {"frames": ["idle_0.png", "idle_1.png"], "fps": 10, "loop": True},
                "attack": {"frames": ["atk_0.png"], "fps": 18, "loop": False},
            }
        }
        frames = MODULE.ordered_frames(manifest)
        self.assertEqual([item["path"] for item in frames], ["idle_0.png", "idle_1.png", "atk_0.png"])
        self.assertEqual([item["state"] for item in frames], ["idle", "idle", "attack"])
        self.assertTrue(frames[0]["loop"])
        self.assertFalse(frames[2]["loop"])

    def test_page_layout_is_deterministic(self):
        layout = MODULE.page_layout(7, 3, 2)
        self.assertEqual(layout[0], {"index": 0, "page": 0, "column": 0, "row": 0})
        self.assertEqual(layout[5], {"index": 5, "page": 0, "column": 2, "row": 1})
        self.assertEqual(layout[6], {"index": 6, "page": 1, "column": 0, "row": 0})

    def test_page_layout_rejects_invalid_dimensions(self):
        with self.assertRaises(ValueError):
            MODULE.page_layout(1, 0, 2)
        with self.assertRaises(ValueError):
            MODULE.page_layout(-1, 2, 2)


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from pathlib import Path

from tools.arcont_lab import confidence_score, parse_simple_graph, validate


class ArcontLabTests(unittest.TestCase):
    def test_simple_graph_parser_handles_canonical_subset(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "graph.yaml"
            p.write_text(
                "engine_commit: ed1daf0bf001b61586d9930840f2f1394092c079\n"
                "nodes:\n"
                "  - id: ARC-SOURCE-A\n"
                "    kind: source-symbol\n"
                "    path: scene/main/node.cpp\n"
                "    symbol: Node\n"
                "  - id: ARC-RULE-B\n"
                "    kind: rule\n"
                "edges:\n"
                "  - from: ARC-RULE-B\n"
                "    to: ARC-SOURCE-A\n"
                "    relation: derived_from\n",
                encoding="utf-8",
            )
            graph = parse_simple_graph(p)
            self.assertEqual(graph["engine_commit"], "ed1daf0bf001b61586d9930840f2f1394092c079")
            self.assertEqual(len(graph["nodes"]), 2)
            self.assertEqual(graph["edges"][0]["relation"], "derived_from")

    def test_validate_rejects_dangling_graph_edge(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            graph_dir = root / "docs" / "godot" / "knowledge"
            graph_dir.mkdir(parents=True)
            (graph_dir / "bad.yaml").write_text(
                "nodes:\n"
                "  - id: ARC-NODE-A\n"
                "    kind: rule\n"
                "edges:\n"
                "  - from: ARC-NODE-A\n"
                "    to: ARC-MISSING\n"
                "    relation: depends_on\n",
                encoding="utf-8",
            )
            errors, _warnings = validate(root)
            self.assertTrue(any("dangling-edge-to" in e for e in errors))

    def test_validate_rejects_broken_markdown_link(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs = root / "docs"
            docs.mkdir()
            (docs / "a.md").write_text("[missing](does-not-exist.md)\n", encoding="utf-8")
            errors, _warnings = validate(root)
            self.assertTrue(any("broken-link" in e for e in errors))

    def test_confidence_is_explicitly_heuristic(self):
        score = confidence_score(1.0, 4, 3, 2, 0, 0)
        self.assertGreater(score["score"], 0)
        self.assertIn("not a probability", score["note"])


if __name__ == "__main__":
    unittest.main()

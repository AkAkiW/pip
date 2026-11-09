import unittest

from src.tree import render_tree

CYCLE = {
    "A": ["B", "C"],
    "B": ["C", "D"],
    "C": ["E"],
    "D": ["E"],
    "E": ["B"],
}


class RenderTreeTest(unittest.TestCase):
    def test_chain(self) -> None:
        lines = render_tree({"A": ["B"], "B": ["C"], "C": []}, "A")
        self.assertEqual(lines, ["A", "`-- B", "    `-- C"])

    def test_root_without_dependencies(self) -> None:
        self.assertEqual(render_tree({"A": []}, "A"), ["A"])

    def test_branch_prefixes(self) -> None:
        lines = render_tree({"A": ["B", "C"], "B": [], "C": []}, "A")
        self.assertEqual(lines, ["A", "|-- B", "`-- C"])

    def test_cycle_is_marked(self) -> None:
        lines = render_tree(CYCLE, "A")
        self.assertIn("|   |       `-- B (cycle)", lines)

    def test_duplicate_subtree_is_not_repeated(self) -> None:
        lines = render_tree(CYCLE, "A")
        self.assertIn("|       `-- E (already listed)", lines)
        self.assertIn("`-- C (already listed)", lines)

    def test_diamond_marks_second_occurrence(self) -> None:
        graph = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
        lines = render_tree(graph, "A")
        self.assertIn("`-- C", lines)
        self.assertIn("    `-- D (already listed)", lines)


if __name__ == "__main__":
    unittest.main()

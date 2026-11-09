import unittest

from src.dot import to_dot


class ToDotTest(unittest.TestCase):
    def test_digraph_wrapper(self) -> None:
        dot = to_dot({"A": ["B"], "B": []})
        self.assertTrue(dot.startswith("digraph dependencies {"))
        self.assertTrue(dot.endswith("}"))

    def test_edges_are_quoted(self) -> None:
        dot = to_dot({"A": ["B"], "B": []})
        self.assertIn('"A" -> "B";', dot)

    def test_leaf_node_is_declared(self) -> None:
        dot = to_dot({"A": ["B"], "B": []})
        self.assertIn('"B";', dot)

    def test_layout_direction(self) -> None:
        dot = to_dot({"A": []})
        self.assertIn("rankdir=LR;", dot)

    def test_output_is_deterministic(self) -> None:
        graph = {"B": ["D", "C"], "A": ["B"], "C": [], "D": []}
        self.assertEqual(to_dot(graph), to_dot(graph))

    def test_special_characters_are_escaped(self) -> None:
        dot = to_dot({'A"B': []})
        self.assertIn('A\\"B', dot)


if __name__ == "__main__":
    unittest.main()

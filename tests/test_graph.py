import unittest

from src.errors import RepositoryError
from src.graph import build_dependency_graph

SOURCE = {
    "A": ["B", "C"],
    "B": ["C", "D"],
    "C": ["E"],
    "D": ["E"],
    "E": ["B"],
}


def source(table):
    def get_dependencies(package):
        return table.get(package, [])

    return get_dependencies


class BuildDependencyGraphTest(unittest.TestCase):
    def test_full_graph_from_a(self) -> None:
        graph = build_dependency_graph(source(SOURCE), "A")
        self.assertEqual(graph["A"], ["B", "C"])
        self.assertEqual(graph["B"], ["C", "D"])
        self.assertEqual(graph["C"], ["E"])
        self.assertEqual(graph["D"], ["E"])
        self.assertEqual(graph["E"], ["B"])
        self.assertEqual(sorted(graph), ["A", "B", "C", "D", "E"])

    def test_cycle_terminates(self) -> None:
        graph = build_dependency_graph(source(SOURCE), "A")
        self.assertEqual(graph["E"], ["B"])

    def test_root_inside_cycle(self) -> None:
        graph = build_dependency_graph(source(SOURCE), "E")
        self.assertEqual(graph["E"], ["B"])
        self.assertEqual(graph["B"], ["C", "D"])
        self.assertEqual(graph["C"], ["E"])

    def test_filter_excludes_subtree(self) -> None:
        graph = build_dependency_graph(source(SOURCE), "A", exclude="D")
        self.assertEqual(graph["A"], ["B", "C"])
        self.assertEqual(graph["B"], ["C"])
        self.assertNotIn("D", graph)

    def test_filter_excludes_leaf(self) -> None:
        graph = build_dependency_graph(source(SOURCE), "A", exclude="C")
        self.assertEqual(graph["A"], ["B"])
        self.assertEqual(graph["B"], ["D"])
        self.assertNotIn("C", graph)

    def test_root_is_always_analyzed(self) -> None:
        graph = build_dependency_graph(source(SOURCE), "A", exclude="A")
        self.assertIn("A", graph)
        self.assertEqual(graph["A"], ["B", "C"])

    def test_empty_exclude_keeps_everything(self) -> None:
        graph = build_dependency_graph(source(SOURCE), "A", exclude="")
        self.assertEqual(len(graph), 5)

    def test_unknown_root_has_no_dependencies(self) -> None:
        graph = build_dependency_graph(source(SOURCE), "Z")
        self.assertEqual(graph, {"Z": []})

    def test_duplicate_dependencies_are_merged(self) -> None:
        table = {"A": ["B", "B", "C"], "B": [], "C": []}
        graph = build_dependency_graph(source(table), "A")
        self.assertEqual(graph["A"], ["B", "C"])

    def test_source_error_names_package(self) -> None:
        def broken(package):
            if package == "B":
                raise RepositoryError("boom")
            return ["B"]

        with self.assertRaises(RepositoryError) as ctx:
            build_dependency_graph(broken, "A")
        self.assertIn("'B'", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

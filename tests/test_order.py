import unittest

from src.graph import build_dependency_graph, load_order

CYCLE = {
    "A": ["B", "C"],
    "B": ["C", "D"],
    "C": ["E"],
    "D": ["E"],
    "E": ["B"],
}

MIXED = {
    "M": ["B", "N"],
    "N": [],
    "B": ["C", "D"],
    "C": ["E"],
    "D": ["E"],
    "E": ["B"],
}


def source(table):
    def get_dependencies(package):
        return table.get(package, [])

    return get_dependencies


class LoadOrderTest(unittest.TestCase):
    def test_chain(self) -> None:
        table = {"I": ["J", "K"], "J": ["K"], "K": []}
        order = load_order(build_dependency_graph(source(table), "I"))
        self.assertEqual(order, ["K", "J", "I"])

    def test_diamond(self) -> None:
        table = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
        order = load_order(build_dependency_graph(source(table), "A"))
        self.assertEqual(order, ["D", "B", "C", "A"])

    def test_cycle_goes_last_sorted(self) -> None:
        graph = build_dependency_graph(source(CYCLE), "A")
        self.assertEqual(load_order(graph), ["A", "B", "C", "D", "E"])

    def test_mixed_cycle_and_chain(self) -> None:
        graph = build_dependency_graph(source(MIXED), "M")
        self.assertEqual(load_order(graph), ["N", "B", "C", "D", "E", "M"])

    def test_single_node(self) -> None:
        order = load_order(build_dependency_graph(source({}), "X"))
        self.assertEqual(order, ["X"])

    def test_dependencies_precede_dependents(self) -> None:
        table = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": ["E"], "E": []}
        graph = build_dependency_graph(source(table), "A")
        order = load_order(graph)
        for name, deps in graph.items():
            for dep in deps:
                self.assertLess(order.index(dep), order.index(name))

    def test_filter_respected_in_order(self) -> None:
        graph = build_dependency_graph(source(CYCLE), "A", exclude="C")
        self.assertEqual(load_order(graph), ["A", "B", "D", "E"])
        self.assertNotIn("C", graph)


if __name__ == "__main__":
    unittest.main()

"""
Tests for the DirectedGraph class.

"""
import unittest

from gc_analyze import DirectedGraph


test_graph = DirectedGraph.from_out_edges(
    vertices=set(range(1, 12)),
    edge_mapper={
        1: [4, 2, 3],
        2: [1],
        3: [5, 6, 7],
        4: [],
        5: [],
        6: [7],
        7: [],
        8: [9],
        9: [10],
        10: [8],
        11: [11],
    },
)


class TestDirectedGraph(unittest.TestCase):
    def test_strongly_connected_components(self):
        for scc in test_graph.strongly_connected_components():
            self.assertIsInstance(scc, DirectedGraph)

    def test_len(self):
        self.assertEqual(len(test_graph), 11)

    def test_children_and_parents(self):
        self.assertItemsEqual(
            test_graph.children(1),
            [2, 3, 4],
        )
        self.assertItemsEqual(
            test_graph.children(7),
            [],
        )
        self.assertItemsEqual(
            test_graph.parents(7),
            [3, 6],
        )
        self.assertItemsEqual(
            test_graph.parents(1),
            [2],
        )

    def test_complete_subgraph_on_vertices(self):
        subgraph = test_graph.complete_subgraph_on_vertices(range(1, 6))
        edges = subgraph.edges
        vertices = subgraph.vertices
        self.assertItemsEqual(vertices, [1, 2, 3, 4, 5])
        self.assertEqual(len(edges), 5)


if __name__ == '__main__':
    unittest.main()

"""
Tests for the DirectedGraph class.

"""
import unittest

from refcycle.directed_graph import DirectedGraph


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


def graph_from_string(s):
    """
    Turn a string like "1 2; 1->2" into a graph.

    """
    vertex_string, edge_string = s.split(';')
    vertices = vertex_string.split()

    edge_pairs = []
    for edge_sequence in edge_string.split():
        sequence_nodes = edge_sequence.split('->')
        for tail, head in zip(sequence_nodes[:-1], sequence_nodes[1:]):
            edge_pairs.append((tail, head))

    return DirectedGraph.from_edge_pairs(vertices, edge_pairs)


def sccs_from_string(s):
    """
    Helper function to make it easy to write lists of scc vertices.

    """
    return [
        set(scc.split())
        for scc in s.split(';')
    ]


test_pairs = [
    (graph_from_string(s1), sccs_from_string(s2))
    for s1, s2 in [
        ("1; 1->1", "1"),
        ("1 2;", "1; 2"),
        ("1 2; 1->2", "1; 2"),
        ("1 2; 1->2 1->2", "1; 2"),
        ("1 2 3; 1->2->3", "1; 2; 3"),
        ("1 2 3; 1->2->3->1", "1 2 3"),
        ("1 2 3; 1->2->1->3->1", "1 2 3"),
        ("1 2 3; 1->2->1", "1 2; 3"),
        ("1 2 3 4; 1->2->4 1->3->4", "1; 2; 3; 4"),
        ("1 2 3 4; 1->2->4 1->3->4->2", "1; 2 4; 3"),
        ("1 2 3 4 5 6 7 8; 1->2->3->4->1 5->6->7->8->5 2->5->8 4->2 ",
         "1 2 3 4; 5 6 7 8"),
        # Example from Tarjan's paper.
        ("1 2 3 4 5 6 7 8; "
         "1->2 2->3 2->8 3->4 3->7 4->5 5->3 5->6 7->4 7->6 8->1 8->7",
         "1 2 8; 3 4 5 7; 6"),
        # Example from Gabow's paper.
        ("1 2 3 4 5 6; 1->2 1->3 2->3 2->4 4->3 4->5 5->2 5->6 6->3 6->4",
         "1; 2 4 5 6; 3"),
    ]
]


class TestDirectedGraph(unittest.TestCase):
    def test_strongly_connected_components(self):
        for test_graph, expected_sccs in test_pairs:
            sccs = test_graph.strongly_connected_components()
            actual_sccs = map(set, sccs)
            self.assertItemsEqual(actual_sccs, expected_sccs)

    def test_strongly_connected_components_deep(self):
        # A deep graph will blow Python's recursion limit with
        # a recursive implementation of the algorithm.
        depth = 10000
        vertices = set(range(depth+1))
        edge_mapper = {i: [i+1] for i in range(depth)}
        edge_mapper[depth] = [0]
        graph = DirectedGraph.from_out_edges(vertices, edge_mapper)
        sccs = graph.strongly_connected_components()
        self.assertEqual(len(sccs), 1)

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

    def test_to_dot(self):
        # No labels.
        dot = test_graph.to_dot()
        self.assertIsInstance(dot, str)

        # Labelled.
        edge_labels = {edge: str(edge) for edge in test_graph.edges}
        vertex_labels = {vertex: str(vertex) for vertex in test_graph.vertices}
        dot = test_graph.to_dot(
            edge_labels=edge_labels,
            vertex_labels=vertex_labels,
        )
        self.assertIsInstance(dot, str)

# Copyright 2013 Mark Dickinson
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Tests for the DirectedGraph class.

"""
import unittest

import six
from six.moves import range

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


def slow_strongly_connected_components(graph):
    """
    Slow-but-sure strongly connected components computation.

    The implementation of IDirectedGraph.strongly_connected_components is
    efficient, but far from straightforward.  This function gives a much slower
    but also much more obviously correct implementation, for comparison and
    testing purposes.

    Returns a list of the strongly connected components of the given graph.

    """
    # Map each vertex to the set of vertices reachable from it.
    # In effect, we're computing the transitive closure of the graph.
    descendants = graph.vertex_dict()
    for v in graph.vertices:
        descendants[v] = graph.descendants(v)

    sccs = []
    identified = graph.vertex_set()
    for v in graph.vertices:
        if v not in identified:
            scc = [w for w in descendants[v] if v in descendants[w]]
            identified.update(scc)
            sccs.append(scc)
    return sccs


class TestDirectedGraph(unittest.TestCase):
    def test_strongly_connected_components(self):
        for test_graph, expected_sccs in test_pairs:
            sccs = test_graph.strongly_connected_components()
            for scc in sccs:
                self.assertIsInstance(scc, DirectedGraph)
            actual_sccs = list(map(set, sccs))
            self.assertCountEqual(actual_sccs, expected_sccs)
            alternative_sccs = [
                set(scc)
                for scc in slow_strongly_connected_components(test_graph)
            ]
            self.assertCountEqual(actual_sccs, alternative_sccs)

    def test_strongly_connected_components_deep(self):
        # A deep graph will blow Python's recursion limit with
        # a recursive implementation of the algorithm.
        depth = 10000
        vertices = set(range(depth + 1))
        edge_mapper = {i: [i + 1] for i in range(depth)}
        edge_mapper[depth] = [0]
        graph = DirectedGraph.from_out_edges(vertices, edge_mapper)
        sccs = graph.strongly_connected_components()
        self.assertEqual(len(sccs), 1)

    def test_limited_descendants(self):
        graph = graph_from_string(
            "1 2 3 4 5 6; 1->2 1->3 2->3 2->4 4->3 4->5 5->2 5->6 6->3 6->4")

        self.assertCountEqual(
            graph.descendants('1', generations=0),
            ['1'],
        )
        self.assertCountEqual(
            graph.descendants('1', generations=1),
            ['1', '2', '3'],
        )
        self.assertCountEqual(
            graph.descendants('1', generations=2),
            ['1', '2', '3', '4'],
        )
        self.assertCountEqual(
            graph.descendants('1', generations=3),
            ['1', '2', '3', '4', '5'],
        )

    def test_more_limited_descendants(self):
        # Regression test for issue #30 on GitHub.  Note that 4 is at depth 2,
        # but with a depth-first search it's likely that the first visit to it
        # will be at depth 3.  So when searching with generations=3, we don't
        # bother looking at the children of 4, so we miss 8.
        graph = graph_from_string(
            "1 2 3 4 5 6 7 8; 1->2->3->4->8 1->5->4 1->6->7->4"
        )

        self.assertCountEqual(
            graph.descendants('1', generations=0),
            ['1'],
        )
        self.assertCountEqual(
            graph.descendants('1', generations=1),
            list('1256'),
        )
        self.assertCountEqual(
            graph.descendants('1', generations=2),
            list('1234567'),
        )
        self.assertCountEqual(
            graph.descendants('1', generations=3),
            list('12345678'),
        )
        self.assertCountEqual(
            graph.descendants('1', generations=4),
            list('12345678'),
        )

    def test_descendants_slow_case(self):
        # Regression test for #48. A buggy earlier version of the
        # descendants method had running time exponential in
        # vertex_count.
        vertex_count = 100
        vertices = set(range(vertex_count))
        edge_mapper = {
            n: [(n + 1) % vertex_count, (n + 1) % vertex_count]
            for n in vertices
        }
        graph = DirectedGraph.from_out_edges(
            vertices=vertices,
            edge_mapper=edge_mapper,
        )
        descendants = graph.descendants(0)
        self.assertEqual(set(descendants), vertices)

    def test_limited_ancestors(self):
        graph = graph_from_string(
            "1 2 3 4 5 6; 1->2 1->3 2->3 2->4 4->3 4->5 5->2 5->6 6->3 6->4")

        self.assertCountEqual(
            graph.ancestors('3', generations=0),
            ['3'],
        )
        self.assertCountEqual(
            graph.ancestors('3', generations=1),
            ['1', '2', '3', '4', '6'],
        )
        self.assertCountEqual(
            graph.ancestors('3', generations=2),
            ['1', '2', '3', '4', '5', '6'],
        )
        self.assertCountEqual(
            graph.ancestors('3', generations=3),
            ['1', '2', '3', '4', '5', '6'],
        )

    def test_ancestors_slow_case(self):
        # Regression test for #48. A buggy earlier version of the
        # ancestors method had running time exponential in
        # vertex_count.
        vertex_count = 100
        vertices = set(range(vertex_count))
        edge_mapper = {
            n: [(n + 1) % vertex_count, (n + 1) % vertex_count]
            for n in vertices
        }
        graph = DirectedGraph.from_out_edges(
            vertices=vertices,
            edge_mapper=edge_mapper,
        )
        ancestors = graph.ancestors(0)
        self.assertEqual(set(ancestors), vertices)

    def test_length(self):
        self.assertEqual(len(test_graph), 11)

    def test_containment(self):
        self.assertIn(2, test_graph)
        self.assertIn(11, test_graph)
        self.assertNotIn(0, test_graph)
        self.assertNotIn(12, test_graph)

    def test_iteration(self):
        self.assertCountEqual(list(test_graph), list(range(1, 12)))

    def test_children_and_parents(self):
        self.assertCountEqual(
            test_graph.children(1),
            [2, 3, 4],
        )
        self.assertCountEqual(
            test_graph.children(7),
            [],
        )
        self.assertCountEqual(
            test_graph.parents(7),
            [3, 6],
        )
        self.assertCountEqual(
            test_graph.parents(1),
            [2],
        )

    def test_full_subgraph(self):
        subgraph = test_graph.full_subgraph(range(1, 6))
        edges = subgraph.edges
        vertices = subgraph.vertices
        self.assertCountEqual(vertices, [1, 2, 3, 4, 5])
        self.assertEqual(len(edges), 5)

    def test_full_subgraph_large_from_list(self):
        # An earlier version of full_subgraph had quadratic-time behaviour.
        vertex_count = 20000
        vertices = set(range(vertex_count))
        edge_mapper = {
            n: [(n + 1) % vertex_count, (n + 1) % vertex_count]
            for n in vertices
        }
        graph = DirectedGraph.from_out_edges(
            vertices=vertices,
            edge_mapper=edge_mapper,
        )
        subgraph = graph.full_subgraph(list(vertices))
        self.assertEqual(len(subgraph.vertices), len(graph.vertices))
        self.assertEqual(len(subgraph.edges), len(graph.edges))

    def test_full_subgraph_from_iterator(self):
        # Should be fine to create a subgraph from an iterator.
        vertex_count = 100
        vertices = set(range(vertex_count))
        edge_mapper = {
            n: [(n + 1) % vertex_count, (n + 1) % vertex_count]
            for n in vertices
        }
        graph = DirectedGraph.from_out_edges(
            vertices=vertices,
            edge_mapper=edge_mapper,
        )
        subgraph = graph.full_subgraph(iter(vertices))
        self.assertEqual(len(subgraph.vertices), len(graph.vertices))
        self.assertEqual(len(subgraph.edges), len(graph.edges))

    def test_to_dot(self):
        dot = test_graph.to_dot()
        self.assertIsInstance(dot, six.text_type)

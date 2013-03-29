import gc
import unittest

from refcycle import ObjectGraph


class A(object):
    pass


def create_cycle():
    a = A()
    b = A()
    a.foo = b
    b.foo = a


class TestObjectGraph(unittest.TestCase):
    def setUp(self):
        self.gc_enabled = True
        if gc.isenabled():
            gc.disable()

    def tearDown(self):
        if gc.isenabled():
            gc.enable()

    def test_empty(self):
        # Two ways to create an empty Object Graph.
        empty_graph = ObjectGraph()
        self.assertEqual(len(empty_graph), 0)
        empty_graph = ObjectGraph([])
        self.assertEqual(len(empty_graph), 0)
        self.assertEqual(list(empty_graph), [])

    def test_single_edge(self):
        a = [0]
        b = [1]
        a.append(b)
        graph = ObjectGraph([a, b])
        self.assertEqual(len(graph), 2)
        self.assertEqual(
            graph.references(),
            [(a, b)],
        )

    def test_self_reference(self):
        a = [0]
        a.append(a)
        graph = ObjectGraph([a])
        self.assertEqual(
            graph.references(),
            [(a, a)],
        )

    def test_multiple_edges(self):
        a = [0]
        b = [1]
        a.append(b)
        a.append(b)
        graph = ObjectGraph([a, b])
        self.assertEqual(
            graph.references(),
            [(a, b), (a, b)],
        )

    def test_simple_cycle(self):
        a = [0]
        b = [1]
        a.append(b)
        b.append(a)
        graph = ObjectGraph([a, b])
        self.assertItemsEqual(
            graph.references(),
            [(a, b), (b, a)],
        )

    def test_length(self):
        a = []
        b = []
        a.append(b)
        graph = ObjectGraph([a, b])
        self.assertEqual(len(graph), 2)

    def test_containment(self):
        a = []
        b = []
        a.append(b)
        graph = ObjectGraph([a])
        self.assertIn(a, graph)
        self.assertNotIn(b, graph)

    def test_iteration(self):
        a = []
        b = []
        a.append(b)
        graph = ObjectGraph([a, b])
        self.assertItemsEqual(list(graph), [a, b])

    def test_repr(self):
        # representation includes the size.
        a = []
        b = []
        a.append(b)
        graph = ObjectGraph([a, b])
        self.assertIn(
            "ObjectGraph object of size 2",
            repr(graph),
        )

    def test_to_dot(self):
        a = []
        b = []
        a.append(b)
        graph = ObjectGraph([a, b])
        self.assertIsInstance(graph.to_dot(), str)

    def test_analyze_simple_cycle(self):
        original_objects = gc.get_objects()
        create_cycle()
        new_objects = gc.get_objects()

        original_ids = set(map(id, original_objects))
        new_objects = [obj for obj in new_objects
                       if id(obj) not in original_ids
                       if obj is not original_objects]

        refgraph = ObjectGraph(new_objects)
        sccs = list(refgraph.strongly_connected_components())
        self.assertEqual(len(sccs), 1)
        self.assertEqual(len(sccs[0]), 4)

    def test_snapshot(self):
        original_objects = ObjectGraph.snapshot()
        create_cycle()
        new_objects = ObjectGraph.snapshot()
        diff = new_objects - original_objects - ObjectGraph(
            original_objects.owned_objects())
        self.assertEqual(len(diff), 4)


if __name__ == '__main__':
    unittest.main()

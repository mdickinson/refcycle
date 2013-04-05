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


def objects_reachable_from(obj):
    found = {}
    to_process = [obj]
    while to_process:
        obj = to_process.pop()
        obj_id = id(obj)
        found[obj_id] = obj
        refs = gc.get_referents(obj)
        for ref in refs:
            if id(ref) not in found:
                to_process.append(ref)
    return ObjectGraph(found.values())


class TestObjectGraph(unittest.TestCase):
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

    def test_children(self):
        a = []
        b = []
        c = []
        d = []
        a.append(b)
        a.append(c)
        b.append(d)
        c.append(d)
        graph = ObjectGraph([a, b, c, d])
        self.assertItemsEqual(graph.children(a), [b, c])
        self.assertItemsEqual(graph.children(b), [d])
        self.assertItemsEqual(graph.children(c), [d])
        self.assertItemsEqual(graph.children(d), [])

    def test_parents(self):
        a = []
        b = []
        c = []
        d = []
        a.append(b)
        a.append(c)
        b.append(d)
        c.append(d)
        graph = ObjectGraph([a, b, c, d])
        self.assertItemsEqual(graph.parents(a), [])
        self.assertItemsEqual(graph.parents(b), [a])
        self.assertItemsEqual(graph.parents(c), [a])
        self.assertItemsEqual(graph.parents(d), [b, c])

    def test_descendants(self):
        a = []
        b = []
        c = []
        d = []
        a.append(b)
        a.append(c)
        b.append(d)
        c.append(d)
        graph = ObjectGraph([a, b, c, d])
        self.assertItemsEqual(graph.descendants(a), [a, b, c, d])
        self.assertItemsEqual(graph.descendants(b), [b, d])
        self.assertItemsEqual(graph.descendants(c), [c, d])
        self.assertItemsEqual(graph.descendants(d), [d])

    def test_ancestors(self):
        a = []
        b = []
        c = []
        d = []
        a.append(b)
        a.append(c)
        b.append(d)
        c.append(d)
        graph = ObjectGraph([a, b, c, d])
        self.assertItemsEqual(graph.ancestors(a), [a])
        self.assertItemsEqual(graph.ancestors(b), [b, a])
        self.assertItemsEqual(graph.ancestors(c), [c, a])
        self.assertItemsEqual(graph.ancestors(d), [d, b, c, a])

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

    def test_long_chain(self):
        # The original recursive algorithms failed on long chains.
        objects = [[]]
        for _ in xrange(10000):
            new_object = []
            objects[-1].append(new_object)
            objects.append(new_object)
        refgraph = ObjectGraph(objects)
        sccs = refgraph.strongly_connected_components()
        self.assertEqual(len(sccs), len(objects))

    def test_annotated_children(self):
        b = (3, 4)
        a = (b, 1, 2, b)
        refgraph = ObjectGraph([a, b])
        children = refgraph.annotated_children(a)
        self.assertItemsEqual(
            children,
            [
                (b, 'item at index 0'),
                (b, 'item at index 3'),
            ],
        )

    def test_annotate_user_defined_object(self):
        class A(object):
            pass

        a = A()
        # Make sure that a.__dict__ exists.
        a.__dict__

        refgraph = objects_reachable_from(a)
        children = refgraph.annotated_children(a)
        self.assertEqual(len(children), 2)
        self.assertItemsEqual(
            children,
            [
                (a.__dict__, "__dict__"),
                (A, "__class__"),
            ],
        )

    def test_annotate_mro(self):
        class A(object):
            pass

        refgraph = objects_reachable_from(A)
        self.assertIn(
            (A.__mro__, "__mro__"),
            refgraph.annotated_children(A),
        )

    def test_annotate_dict_values(self):
        d = {'mylist': [1, 2, 3]}

        refgraph = objects_reachable_from(d)
        self.assertIn(
            (d['mylist'], "value for key mylist"),
            refgraph.annotated_children(d),
        )

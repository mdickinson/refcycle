"""
General tests for the refcycle package.

"""
import gc
import unittest

from refcycle import (
    cycles_created_by,
    disable_gc,
    garbage,
    ObjectGraph,
    objects_reachable_from,
    snapshot,
)


class A(object):
    pass


def create_cycles():
    a = A()
    b = A()
    a.foo = b
    b.foo = a


class TestRefcycle(unittest.TestCase):
    def setUp(self):
        # Ensure gc.garbage contains as little as possible.
        del gc.garbage[:]
        gc.collect()

    def test_cycles_created_by(self):
        original_garbage = len(gc.garbage)

        object_graph = cycles_created_by(create_cycles)
        # Cycle consists of the two objects and their attribute dictionaries.
        self.assertEqual(len(object_graph), 4)
        self.assertEqual(len(object_graph.references()), 4)

        # Case where no cycles created.
        object_graph = cycles_created_by(lambda: None)
        self.assertEqual(len(object_graph), 0)

        # Check that we didn't unnecessarily add anything to gc.garbage.
        self.assertEqual(len(gc.garbage), original_garbage)


    def test_snapshot(self):
        with disable_gc():
            original_objects = snapshot()
            create_cycles()
            new_objects = snapshot()
            diff = new_objects - original_objects - ObjectGraph(
                original_objects.owned_objects())
            self.assertEqual(len(diff), 4)

    def test_disable_gc(self):
        self.assertTrue(gc.isenabled())
        with disable_gc():
            self.assertFalse(gc.isenabled())
        self.assertTrue(gc.isenabled())

        gc.disable()

        self.assertFalse(gc.isenabled())
        with disable_gc():
            self.assertFalse(gc.isenabled())
        self.assertFalse(gc.isenabled())

        gc.enable()

    def test_objects_reachable_from(self):
        a = []
        b = []
        a.append(b)
        graph = objects_reachable_from(a)
        self.assertItemsEqual(
            list(graph),
            [a, b],
        )

    def test_garbage(self):
        with disable_gc():
            a = []
            b = []
            c = []
            a.append(a)
            b.append(c)
            c.append(b)
            del a, b, c

            graph = garbage()
            self.assertEqual(len(gc.garbage), 0)
            self.assertEqual(len(graph), 3)

            # A second call to garbage should
            # produce nothing new.
            graph2 = garbage()
            self.assertEqual(gc.garbage, [])
            self.assertEqual(len(graph2), 0)

            # But if we delete graph then
            # a, b and c become collectable again.
            del graph
            graph = garbage()
            self.assertEqual(gc.garbage, [])
            self.assertEqual(len(graph), 3)

            # Get rid of everything.
            del graph, graph2
            gc.collect()
            graph = garbage()
            self.assertEqual(gc.garbage, [])
            self.assertEqual(len(graph), 0)

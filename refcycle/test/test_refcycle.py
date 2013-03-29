"""
General tests for the refcycle package.

"""
import gc
import unittest

from refcycle import cycles_created_by, snapshot, ObjectGraph
from refcycle import disable_gc


class A(object):
    pass


def create_cycles():
    a = A()
    b = A()
    a.foo = b
    b.foo = a


class TestRefcycle(unittest.TestCase):
    def test_cycles_created_by(self):
        object_graph = cycles_created_by(create_cycles)
        # Cycle consists of the two objects and their attribute dictionaries.
        self.assertEqual(len(object_graph), 4)
        self.assertEqual(len(object_graph.references()), 4)

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


if __name__ == '__main__':
    unittest.main()

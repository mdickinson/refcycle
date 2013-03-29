"""
General tests for the refcycle package.

"""
import unittest

from refcycle import cycles_created_by


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


if __name__ == '__main__':
    unittest.main()

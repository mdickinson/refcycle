import gc
import unittest

from gc_analyze import RefGraph


class A(object):
    pass


def create_cycle():
    a = A()
    b = A()
    a.foo = b
    b.foo = a


class TestGcAnalyze(unittest.TestCase):
    def setUp(self):
        self.gc_enabled = True
        if gc.isenabled():
            gc.disable()

    def tearDown(self):
        if gc.isenabled():
            gc.enable()

    def test_analyze_simple_cycle(self):
        original_objects = gc.get_objects()
        create_cycle()
        new_objects = gc.get_objects()

        original_ids = set(map(id, original_objects))
        new_objects = [obj for obj in new_objects
                       if id(obj) not in original_ids
                       if obj is not original_objects]

        refgraph = RefGraph.from_objects(new_objects)
        sccs = list(refgraph.strongly_connected_components())
        self.assertEqual(len(sccs), 1)
        self.assertEqual(len(sccs[0]), 4)

    def test_snapshot(self):
        original_objects = RefGraph.snapshot()
        create_cycle()
        new_objects = RefGraph.snapshot()
        diff = new_objects - original_objects - RefGraph.from_objects(
            original_objects.owned_objects())
        self.assertEqual(len(diff), 4)


if __name__ == '__main__':
    unittest.main()

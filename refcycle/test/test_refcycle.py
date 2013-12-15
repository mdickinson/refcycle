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
General tests for the refcycle package.

"""
import gc
import unittest

from refcycle import (
    cycles_created_by,
    garbage,
    ObjectGraph,
    objects_reachable_from,
    snapshot,
    key_cycles,
)
from refcycle.gc_utils import restore_gc_state


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
        with restore_gc_state():
            gc.disable()
            original_objects = snapshot()
            create_cycles()
            new_objects = snapshot()
            diff = new_objects - original_objects - ObjectGraph(
                original_objects.owned_objects())
            self.assertEqual(len(diff), 4)

    def test_objects_reachable_from(self):
        a = []
        b = []
        a.append(b)
        graph = objects_reachable_from(a)
        self.assertCountEqual(
            list(graph),
            [a, b],
        )

    def test_garbage(self):
        with restore_gc_state():
            gc.disable()
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

    def test_key_cycles(self):
        with restore_gc_state():
            gc.disable()
            a = ['a']
            b = ['b']
            c = ['c']
            d = ['d']
            a.append(b)
            b.append(a)
            c.append(d)
            d.append(c)
            b.append(d)
            del a, b, c, d

            sccs = key_cycles()
            self.assertEqual(len(sccs), 1)
            self.assertEqual(len(sccs[0]), 2)
            # Make sure to remove the sccs for good.
            del sccs
            gc.collect()

        # Same again, but with no connections between {a, b} and {c, d}.
        with restore_gc_state():
            gc.disable()
            a = ['a']
            b = ['b']
            c = ['c']
            d = ['d']
            a.append(b)
            b.append(a)
            c.append(d)
            d.append(c)
            del a, b, c, d

            sccs = key_cycles()
            self.assertEqual(len(sccs), 2)
            self.assertEqual(len(sccs[0]), 2)
            self.assertEqual(len(sccs[1]), 2)
            # Make sure to remove the sccs for good.
            del sccs
            gc.collect()

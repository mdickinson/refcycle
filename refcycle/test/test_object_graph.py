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
import collections
import gc
import json
import os
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

import six
from six.moves import range

from refcycle.creators import objects_reachable_from
from refcycle.i_directed_graph import IDirectedGraph
from refcycle.object_graph import ObjectGraph


def dot_available():
    """
    Return True if the Graphviz 'dot' command is available and in the path,
    else False.

    """
    try:
        output = subprocess.check_output(
            ['dot', '-V'],
            stderr=subprocess.STDOUT)
    except (OSError, subprocess.CalledProcessError):
        return False
    return b'graphviz' in output.lower()


def is_svg(filename):
    """
    Return True if the given file appears to be an SVG file, else False.

    """
    # Grab first opening tag.
    with open(filename, "r") as f:
        try:
            start_events = ET.iterparse(f, events=('start',))
            _, element = next(start_events)
        except (ET.ParseError, StopIteration):
            return False

    # And check that it's the expected one.
    return element.tag == '{http://www.w3.org/2000/svg}svg'


class A(object):
    pass


def create_cycle():
    a = A()
    b = A()
    a.foo = b
    b.foo = a


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

    def test_construction_from_iterator(self):
        a = [0]
        b = [1]
        a.append(b)
        b.append(a)
        objects = iter([a, b, a[0], b[0]])
        graph = ObjectGraph(objects)
        self.assertEqual(len(graph), 4)
        # Check that we get all the edges we expect.
        self.assertEqual(len(graph.children(a)), 2)
        self.assertEqual(len(graph.children(b)), 2)

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
        self.assertCountEqual(
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
        self.assertCountEqual(list(graph), [a, b])

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
        self.assertCountEqual(graph.children(a), [b, c])
        self.assertCountEqual(graph.children(b), [d])
        self.assertCountEqual(graph.children(c), [d])
        self.assertCountEqual(graph.children(d), [])

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
        self.assertCountEqual(graph.parents(a), [])
        self.assertCountEqual(graph.parents(b), [a])
        self.assertCountEqual(graph.parents(c), [a])
        self.assertCountEqual(graph.parents(d), [b, c])

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
        self.assertCountEqual(graph.descendants(a), [a, b, c, d])
        self.assertCountEqual(graph.descendants(b), [b, d])
        self.assertCountEqual(graph.descendants(c), [c, d])
        self.assertCountEqual(graph.descendants(d), [d])

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
        self.assertCountEqual(graph.ancestors(a), [a])
        self.assertCountEqual(graph.ancestors(b), [b, a])
        self.assertCountEqual(graph.ancestors(c), [c, a])
        self.assertCountEqual(graph.ancestors(d), [d, b, c, a])

    def test_shortest_path(self):
        # Looking for paths from a to f, we have:
        #     a -> b -> e -> f
        #     a -> c -> f (shortest)
        a = []
        b = []
        c = []
        d = []
        e = []
        f = []
        a.append(b)
        a.append(c)
        a.append(d)
        b.append(e)
        e.append(f)
        c.append(f)
        graph = ObjectGraph([a, b, c, d, e, f])
        path = graph.shortest_path(a, f)
        self.assertIsInstance(path, IDirectedGraph)
        self.assertEqual(len(path), 3)

        self.assertIn(a, path.vertices)
        self.assertIn(c, path.vertices)
        self.assertIn(f, path.vertices)

    def test_shortest_path_no_path(self):
        a = []
        b = []
        c = []
        a.append(b)
        c.append(b)
        graph = ObjectGraph([a, b, c])
        with self.assertRaises(ValueError):
            graph.shortest_path(a, c)

    def test_shortest_path_start_equals_end(self):
        a = []
        b = []
        a.append(b)
        b.append(a)
        a.append(a)
        graph = ObjectGraph([a, b])
        path = graph.shortest_path(a, a)
        self.assertIsInstance(path, IDirectedGraph)
        self.assertEqual(len(path), 1)

    def test_shortest_cycle(self):
        a = []
        b = []
        a.append(b)
        b.append(a)
        graph = ObjectGraph([a, b])
        cycle = graph.shortest_cycle(a)
        self.assertIsInstance(cycle, IDirectedGraph)
        self.assertEqual(len(cycle), 2)

    def test_shortest_cycle_self_cycle(self):
        a = []
        b = []
        c = []
        a.append(b)
        b.append(b)
        b.append(c)
        c.append(a)
        graph = ObjectGraph([a, b, c])
        cycle = graph.shortest_cycle(b)
        self.assertIsInstance(cycle, IDirectedGraph)
        self.assertEqual(len(cycle), 1)

    def test_shortest_cycle_no_cycle(self):
        a = []
        b = []
        c = []
        b.append(c)
        c.append(b)
        a.append(b)
        graph = ObjectGraph([a, b, c])
        with self.assertRaises(ValueError):
            graph.shortest_cycle(a)

    def test_shortest_cycle_many_cycles(self):
        a, b, c, d, e = objs = [[] for _ in range(5)]
        a.append(b)
        b.append(c)
        c.append(a)
        b.append(d)
        d.append(a)
        b.append(e)
        e.append(d)
        graph = ObjectGraph(objs)
        cycle = graph.shortest_cycle(a)
        self.assertIsInstance(cycle, IDirectedGraph)
        self.assertEqual(len(cycle), 3)
        self.assertIn(a, cycle)
        self.assertIn(b, cycle)
        # Exactly one of c and d should be in the cycle.
        self.assertEqual((c in cycle) + (d in cycle), 1)

    def test_count_by_typename(self):
        a, b, c = [], [], []
        d, e = set(), set()
        f = {}
        graph = ObjectGraph([a, b, c, d, e, f])
        counts = graph.count_by_typename()
        self.assertIsInstance(counts, collections.Counter)
        self.assertEqual(
            dict(counts),
            dict(list=3, set=2, dict=1),
        )

    def test_find_by_typename(self):
        a, b, c = [], [], []
        d, e = set(), set()
        f = {}
        graph = ObjectGraph([a, b, c, d, e, f])

        sets = graph.find_by_typename('set')
        self.assertEqual(len(sets), 2)
        self.assertIn(d, sets)
        self.assertIn(e, sets)

    def test_to_dot(self):
        a = []
        b = []
        a.append(b)
        graph = ObjectGraph([a, b])
        dot = graph.to_dot()
        self.assertIn(
            "{} -> {} [label=\"item[0]\"];".format(id(a), id(b)),
            dot,
        )
        self.assertIn(
            "{} [label=\"list[1]\"];".format(id(a)),
            dot,
        )
        self.assertIn(
            "{} [label=\"list[0]\"];".format(id(b)),
            dot,
        )
        self.assertIsInstance(dot, six.text_type)

    def test_to_json(self):
        # XXX Needs a better test.  For now, just exercise the
        # to_json method.
        a = []
        b = []
        a.append(b)
        graph = ObjectGraph([a, b])
        json_graph = graph.to_json()
        self.assertIsInstance(json_graph, six.text_type)
        # Make sure that the result is valid json.
        json.loads(json_graph)

    def test_export_json(self):
        graph = objects_reachable_from([[1, 2, 3], [4, [5, 6]]])
        tempdir = tempfile.mkdtemp()
        try:
            filename = os.path.join(tempdir, 'output.json')
            graph.export_json(filename)
            self.assertTrue(os.path.exists(filename))
        finally:
            shutil.rmtree(tempdir)

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
        for _ in range(10000):
            new_object = []
            objects[-1].append(new_object)
            objects.append(new_object)
        refgraph = ObjectGraph(objects)
        sccs = refgraph.strongly_connected_components()
        self.assertEqual(len(sccs), len(objects))

    def test_intersection(self):
        a = []
        b = []
        c = []
        d = []
        c.append(d)
        a.append(c)
        b.append(c)
        a.append(a)
        graph1 = ObjectGraph([a, c, d])
        graph2 = ObjectGraph([b, c, d])
        intersection = graph1 & graph2
        self.assertEqual(len(intersection), 2)
        self.assertIn(c, intersection)
        self.assertIn(d, intersection)
        self.assertNotIn(a, intersection)
        self.assertNotIn(b, intersection)

    def test_subtraction(self):
        a = []
        b = []
        c = []
        d = []
        c.append(d)
        a.append(c)
        b.append(c)
        a.append(a)
        graph1 = ObjectGraph([a, c, d])
        graph2 = ObjectGraph([b, c, d])
        difference = graph1 - graph2
        self.assertEqual(len(difference), 1)
        self.assertIn(a, difference)
        self.assertNotIn(b, difference)
        self.assertNotIn(c, difference)
        self.assertNotIn(d, difference)

    def test_sccs(self):
        a, b, c, d = ['A'], ['B'], ['C'], ['D']
        a.append(b)
        b.append(a)
        c.append(d)
        d.append(c)
        b.append(d)
        graph = ObjectGraph([a, b, c, d])

        sccs = graph.strongly_connected_components()
        self.assertEqual(len(sccs), 2)
        self.assertEqual(len(sccs[0]), 2)
        self.assertEqual(len(sccs[1]), 2)

        # Identify the two sccs.
        scc_ab = next(scc for scc in sccs if a in scc)
        scc_cd = next(scc for scc in sccs if c in scc)
        self.assertIn(a, scc_ab)
        self.assertIn(b, scc_ab)
        self.assertNotIn(c, scc_ab)
        self.assertNotIn(d, scc_ab)

        self.assertNotIn(a, scc_cd)
        self.assertNotIn(b, scc_cd)
        self.assertIn(c, scc_cd)
        self.assertIn(d, scc_cd)

        # Check that they've got the expected edges.
        self.assertEqual(scc_ab.children(a), [b])
        self.assertEqual(scc_ab.children(b), [a])
        self.assertEqual(scc_cd.children(c), [d])
        self.assertEqual(scc_cd.children(d), [c])

    def test_source_components(self):
        # Single source consisting of two objects.
        a, b, c, d = ['A'], ['B'], ['C'], ['D']
        a.append(b)
        b.append(a)
        c.append(d)
        d.append(c)
        b.append(d)
        graph = ObjectGraph([a, b, c, d])
        sources = graph.source_components()
        self.assertEqual(len(sources), 1)
        source = sources[0]
        self.assertIn(a, source)
        self.assertIn(b, source)
        self.assertNotIn(c, source)
        self.assertNotIn(d, source)

        # Single source consisting of one object.
        a, b, c, d = ['A'], ['B'], ['C'], ['D']
        a.append(b)
        b.append(d)
        c.append(a)
        graph = ObjectGraph([a, b, c, d])
        sources = graph.source_components()
        self.assertEqual(len(sources), 1)
        source = sources[0]
        self.assertNotIn(a, source)
        self.assertNotIn(b, source)
        self.assertIn(c, source)
        self.assertNotIn(d, source)

        # Multiple sources.
        a, b, c, d, e, f = ['A'], ['B'], ['C'], ['D'], ['E'], ['F']
        a.append(b)
        b.append(d)
        c.append(a)
        e.append(d)

        graph = ObjectGraph([a, b, c, d, e, f])
        sources = graph.source_components()
        self.assertEqual(len(sources), 3)

    def test_abstract_bases(self):
        graph = ObjectGraph()
        self.assertIsInstance(graph, IDirectedGraph)
        self.assertIsInstance(graph, collections.Sized)
        self.assertIsInstance(graph, collections.Iterable)
        self.assertIsInstance(graph, collections.Container)

    @unittest.skipUnless(dot_available(), "Graphviz dot command not available")
    def test_export_image(self):
        graph = objects_reachable_from([[1, 2, 3], [4, [5, 6]]])
        tempdir = tempfile.mkdtemp()
        try:
            filename = os.path.join(tempdir, 'output.png')
            graph.export_image(filename)
            self.assertTrue(os.path.exists(filename))
        finally:
            shutil.rmtree(tempdir)

    @unittest.skipUnless(dot_available(), "Graphviz dot command not available")
    def test_export_image_implicit_format(self):
        graph = objects_reachable_from([[1, 2, 3], [4, [5, 6]]])
        tempdir = tempfile.mkdtemp()
        try:
            filename = os.path.join(tempdir, 'output.svg')
            graph.export_image(filename)
            self.assertTrue(os.path.exists(filename))
            self.assertTrue(is_svg(filename))
        finally:
            shutil.rmtree(tempdir)

    @unittest.skipUnless(dot_available(), "Graphviz dot command not available")
    def test_export_image_explicit_format(self):
        graph = objects_reachable_from([[1, 2, 3], [4, [5, 6]]])
        tempdir = tempfile.mkdtemp()
        try:
            # Deliberately using a misleading extension...
            filename = os.path.join(tempdir, 'output.png')
            graph.export_image(filename, format='svg')
            self.assertTrue(os.path.exists(filename))
            self.assertTrue(is_svg(filename))
        finally:
            shutil.rmtree(tempdir)

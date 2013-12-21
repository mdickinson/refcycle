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
import os
import shutil
import tempfile
import unittest

import six

from refcycle.annotated_graph import (
    AnnotatedEdge,
    AnnotatedGraph,
    AnnotatedVertex,
)


class TestAnnotatedGraph(unittest.TestCase):
    def test_simple_graph_construction(self):
        # Direct construction of a simple annotated graph.
        v1 = AnnotatedVertex(id=0, annotation="vertex 1")
        v2 = AnnotatedVertex(id=1, annotation="vertex 2")
        e1 = AnnotatedEdge(
            id=3,
            annotation="edge from vertex 1 to vertex 2",
            tail=0,
            head=1,
        )
        graph = AnnotatedGraph(
            vertices=[v1, v2],
            edges=[e1],
        )
        self.assertEqual(len(graph.vertices), 2)
        self.assertEqual(len(graph.edges), 1)
        self.assertCountEqual(graph.children(v1), [v2])
        self.assertCountEqual(graph.parents(v2), [v1])

    def test_strongly_connected_components(self):
        # Direct construction of a simple annotated graph.
        graph = AnnotatedGraph(
            vertices=[
                AnnotatedVertex(id=0, annotation="vertex 1"),
                AnnotatedVertex(id=1, annotation="vertex 2"),
            ],
            edges=[
                AnnotatedEdge(
                    id=3,
                    annotation="from 1 to 2",
                    head=0,
                    tail=1,
                ),
            ],
        )
        self.assertEqual(len(graph.vertices), 2)
        sccs = graph.strongly_connected_components()
        self.assertEqual(len(sccs), 2)
        self.assertEqual(len(sccs[0]), 1)
        self.assertEqual(len(sccs[1]), 1)
        self.assertIsInstance(sccs[0], AnnotatedGraph)
        self.assertIsInstance(sccs[1], AnnotatedGraph)

    def test_to_json(self):
        graph = AnnotatedGraph(
            vertices=[
                AnnotatedVertex(id=0, annotation="vertex 1"),
                AnnotatedVertex(id=1, annotation="vertex 2"),
            ],
            edges=[
                AnnotatedEdge(
                    id=3,
                    annotation="from 1 to 2",
                    head=0,
                    tail=1,
                ),
            ],
        )
        json = graph.to_json()
        self.assertIsInstance(json, six.text_type)
        reconstructed = AnnotatedGraph.from_json(json)
        self.assertIsInstance(reconstructed, AnnotatedGraph)
        self.assertEqual(len(reconstructed), 2)

        for vertex in graph:
            self.assertIn(vertex, reconstructed)
        for vertex in reconstructed:
            self.assertIn(vertex, graph)

    def test_export_import_json(self):
        graph = AnnotatedGraph(
            vertices=[
                AnnotatedVertex(id=0, annotation="vertex 1"),
                AnnotatedVertex(id=1, annotation="vertex 2"),
            ],
            edges=[
                AnnotatedEdge(
                    id=3,
                    annotation="from 1 to 2",
                    head=0,
                    tail=1,
                ),
            ],
        )

        tempdir = tempfile.mkdtemp()
        try:
            filename = os.path.join(tempdir, 'output.json')
            graph.export_json(filename)
            self.assertTrue(os.path.exists(filename))
            reconstructed = AnnotatedGraph.import_json(filename)
        finally:
            shutil.rmtree(tempdir)

        self.assertIsInstance(reconstructed, AnnotatedGraph)
        self.assertEqual(len(reconstructed), 2)
        for vertex in graph:
            self.assertIn(vertex, reconstructed)
        for vertex in reconstructed:
            self.assertIn(vertex, graph)

    def test_dot_quoting(self):
        # Check that labels are properly quoted.
        graph = AnnotatedGraph(
            vertices=[
                AnnotatedVertex(id=0, annotation='vertex "1"'),
                AnnotatedVertex(id=1, annotation='vertex "2"'),
            ],
            edges=[
                AnnotatedEdge(
                    id=3,
                    annotation='from "1" to "2"',
                    head=0,
                    tail=1,
                ),
            ],
        )

        dot = graph.to_dot()
        self.assertIsInstance(dot, six.text_type)
        self.assertIn(r'"vertex \"1\""', dot)
        self.assertIn(r'"from \"1\" to \"2\""', dot)

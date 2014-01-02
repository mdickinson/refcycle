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
from __future__ import unicode_literals

import collections
import json
import os
import subprocess

import six

from refcycle.i_directed_graph import IDirectedGraph


DOT_DIGRAPH_TEMPLATE = """\
digraph G {{
{edges}\
{vertices}\
}}
"""
DOT_VERTEX_TEMPLATE = "    {vertex} [label={label}];\n"
DOT_EDGE_TEMPLATE = "    {start} -> {stop};\n"
DOT_LABELLED_EDGE_TEMPLATE = "    {start} -> {stop} [label={label}];\n"


def dot_quote(s):
    """
    Return a quoted version of a (unicode) string s suitable for output in the
    DOT language.

    """
    # From the documentation (http://www.graphviz.org/doc/info/lang.html):
    #
    # In quoted strings in DOT, the only escaped character is double-quote
    # ("). That is, in quoted strings, the dyad \" is converted to "; all other
    # characters are left unchanged. In particular, \\ remains \\. Layout
    # engines may apply additional escape sequences.
    return "\"{}\"".format(s.replace("\"", "\\\""))


class AnnotatedEdge(object):
    __slots__ = ('id', 'annotation', 'head', 'tail')

    def __new__(cls, id, annotation, head, tail):
        # Head and tail refer to the integer ids of the corresponding
        # vertices, and not to the vertices themselves.
        self = object.__new__(cls)
        self.id = id
        self.annotation = annotation
        self.head = head
        self.tail = tail
        return self

    def __eq__(self, other):
        if not isinstance(other, AnnotatedEdge):
            return False
        return self.id == other.id

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return self.id


class AnnotatedVertex(object):
    __slots__ = ('id', 'annotation')

    def __new__(cls, id, annotation):
        self = object.__new__(cls)
        self.id = id
        self.annotation = annotation
        return self

    def __eq__(self, other):
        if not isinstance(other, AnnotatedVertex):
            return False
        return self.id == other.id

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return self.id


class AnnotatedGraph(IDirectedGraph):
    """
    A directed graph whose vertices and edges carry annotations.

    The vertices and edges are instances of AnnotatedVertex and AnnotatedEdge
    respectively.  Each such vertex or edge has both an integral ``id`` and a
    string ``annotation``.

    """
    ###########################################################################
    ### IDirectedGraph interface.
    ###########################################################################

    def head(self, edge):
        """
        Return the head of the given edge.

        """
        return self._obj_map[edge.head]

    def tail(self, edge):
        """
        Return the tail of the given edge.

        """
        return self._obj_map[edge.tail]

    def out_edges(self, vertex):
        """
        Return a list of the edges leaving this vertex.

        """
        return self._out_edges[vertex.id]

    def in_edges(self, vertex):
        """
        Return a list of the edges entering this vertex.

        """
        return self._in_edges[vertex.id]

    @property
    def vertices(self):
        """
        Return collection of vertices of the graph.

        """
        return self._vertices

    @property
    def edges(self):
        """
        Return collection of edges of the graph.

        """
        return self._edges

    def full_subgraph(self, vertices):
        """
        Return the subgraph of this graph whose vertices
        are the given ones and whose edges are the edges
        of the original graph between those vertices.

        """
        obj_map = {vertex.id: vertex for vertex in vertices}
        edges = [
            edge for vertex_id in obj_map
            for edge in self._out_edges[vertex_id]
            if edge.head in obj_map
        ]

        return AnnotatedGraph(
            vertices=obj_map.values(),
            edges=edges,
        )

    ###########################################################################
    ### AnnotatedGraph constructors.
    ###########################################################################

    def __new__(cls, vertices, edges):
        self = object.__new__(cls)
        self._vertices = set(vertices)
        self._edges = set(edges)

        self._obj_map = {
            vertex.id: vertex for vertex in vertices
        }

        self._out_edges = collections.defaultdict(list)
        self._in_edges = collections.defaultdict(list)
        for edge in self._edges:
            self._out_edges[edge.tail].append(edge)
            self._in_edges[edge.head].append(edge)

        return self

    ###########################################################################
    ### JSON serialization.
    ###########################################################################

    def to_json(self):
        """
        Convert to a JSON string.

        """
        obj = {
            "vertices": [
                {
                    "id": vertex.id,
                    "annotation": vertex.annotation,
                }
                for vertex in self.vertices
            ],
            "edges": [
                {
                    "id": edge.id,
                    "annotation": edge.annotation,
                    "head": edge.head,
                    "tail": edge.tail,
                }
                for edge in self._edges
            ],
        }
        # Ensure that we always return unicode output on Python 2.
        return six.text_type(json.dumps(obj, ensure_ascii=False))

    @classmethod
    def from_json(cls, json_graph):
        """
        Reconstruct the graph from a graph exported to JSON.

        """
        obj = json.loads(json_graph)

        vertices = [
            AnnotatedVertex(
                id=vertex["id"],
                annotation=vertex["annotation"],
            )
            for vertex in obj["vertices"]
        ]

        edges = [
            AnnotatedEdge(
                id=edge["id"],
                annotation=edge["annotation"],
                head=edge["head"],
                tail=edge["tail"],
            )
            for edge in obj["edges"]
        ]

        return cls(vertices=vertices, edges=edges)

    def export_json(self, filename):
        """
        Export graph in JSON form to the given file.

        """
        json_graph = self.to_json()
        with open(filename, 'wb') as f:
            f.write(json_graph.encode('utf-8'))

    @classmethod
    def import_json(cls, filename):
        """
        Import graph from the given file.  The file is expected
        to contain UTF-8 encoded JSON data.

        """
        with open(filename, 'rb') as f:
            json_graph = f.read().decode('utf-8')
        return cls.from_json(json_graph)

    ###########################################################################
    ### Graphviz output.
    ###########################################################################

    def _format_edge(self, edge_labels, edge):
        label = edge_labels.get(edge.id)
        if label is not None:
            template = DOT_LABELLED_EDGE_TEMPLATE
            return template.format(
                start=edge.tail,
                stop=edge.head,
                label=dot_quote(label),
            )
        else:
            template = DOT_EDGE_TEMPLATE
            return template.format(
                start=edge.tail,
                stop=edge.head,
            )

    def to_dot(self):
        """
        Produce a graph in DOT format.

        """
        edge_labels = {
            edge.id: edge.annotation
            for edge in self._edges
        }

        edges = [self._format_edge(edge_labels, edge) for edge in self._edges]

        vertices = [
            DOT_VERTEX_TEMPLATE.format(
                vertex=vertex.id,
                label=dot_quote(vertex.annotation),
            )
            for vertex in self.vertices
        ]

        return DOT_DIGRAPH_TEMPLATE.format(
            edges="".join(edges),
            vertices="".join(vertices),
        )

    def export_image(self, filename='refcycle.png', format=None,
                     dot_executable='dot'):
        """
        Export graph as an image.

        This requires that Graphviz is installed and that the ``dot``
        executable is in your path.

        The *filename* argument specifies the output filename.

        The *format* argument lets you specify the output format.  It may be
        any format that ``dot`` understands, including extended format
        specifications like ``png:cairo``.  If omitted, the filename extension
        will be used; if no filename extension is present, ``png`` will be
        used.

        The *dot_executable* argument lets you provide a full path to the
        ``dot`` executable if necessary.

        """
        # Figure out what output format to use.
        if format is None:
            _, extension = os.path.splitext(filename)
            if extension.startswith('.') and len(extension) > 1:
                format = extension[1:]
            else:
                format = 'png'

        # Convert to 'dot' format.
        dot_graph = self.to_dot()

        # We'll send the graph directly to the process stdin.
        cmd = [
            dot_executable,
            '-T{}'.format(format),
            '-o{}'.format(filename),
        ]
        dot = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        dot.communicate(dot_graph.encode('utf-8'))

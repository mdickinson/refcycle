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
import json

from refcycle.i_directed_graph import IDirectedGraph


DOT_DIGRAPH_TEMPLATE = """\
digraph G {{
{edges}\
{vertices}\
}}
"""
DOT_VERTEX_TEMPLATE = "    {vertex} [label=\"{label}\"];\n"
DOT_EDGE_TEMPLATE = "    {start} -> {stop};\n"
DOT_LABELLED_EDGE_TEMPLATE = "    {start} -> {stop} [label=\"{label}\"];\n"


class AnnotatedEdge(object):
    def __new__(cls, id, annotation, head, tail):
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
        vertex_ids = {vertex.id for vertex in vertices}
        edges = [
            edge for edge in self._edges
            if edge.tail in vertex_ids
            if edge.head in vertex_ids
        ]

        return AnnotatedGraph(
            vertices=vertices,
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

    def export_json(self):
        """
        Export this graph in JSON format.

        """
        obj = {
            'vertices': [
                {
                    'id': vertex.id,
                    'annotation': vertex.annotation,
                }
                for vertex in self.vertices
            ],
            'edges': [
                {
                    'id': edge.id,
                    'annotation': edge.annotation,
                    'head': edge.head,
                    'tail': edge.tail,
                }
                for edge in self._edges
            ],
        }
        return json.dumps(obj)

    @classmethod
    def from_json(cls, json_graph):
        """
        Reconstruct the graph from a graph exported to JSON.

        """
        obj = json.loads(json_graph)

        vertices = [
            AnnotatedVertex(
                id=vertex['id'],
                annotation=vertex['annotation'],
            )
            for vertex in obj['vertices']
        ]

        edges = [
            AnnotatedEdge(
                id=edge['id'],
                annotation=edge['annotation'],
                head=edge['head'],
                tail=edge['tail'],
            )
            for edge in obj['edges']
        ]

        return cls(vertices=vertices, edges=edges)

    ###########################################################################
    ### GraphViz output.
    ###########################################################################

    def _format_edge(self, edge_labels, edge):
        label = edge_labels.get(edge.id)
        if label is not None:
            template = DOT_LABELLED_EDGE_TEMPLATE
        else:
            template = DOT_EDGE_TEMPLATE
        return template.format(
            start=edge.tail,
            stop=edge.head,
            label=label,
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
                label=vertex.annotation,
            )
            for vertex in self.vertices
        ]

        return DOT_DIGRAPH_TEMPLATE.format(
            edges=''.join(edges),
            vertices=''.join(vertices),
        )

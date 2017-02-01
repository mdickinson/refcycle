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
A 'DirectedGraph' is an object representing a simple directed graph.

A directed graph consists of:

  - a collection of vertices
  - a collection of edges
  - a mapping 'heads' from edges to vertices
  - a mapping 'tails' from edges to vertices

This setup allows for self-edges, and multiple edges between a pair of
vertices.  Since we want to use these directed graphs to represent references
between Python objects, both these capabilities are necessary.

"""
import collections
import itertools

import six

from refcycle.annotated_graph import (
    AnnotatedEdge,
    AnnotatedGraph,
    AnnotatedVertex,
)
from refcycle.i_directed_graph import IDirectedGraph


class DirectedGraph(IDirectedGraph):
    """
    Object representing a directed graph.

    `vertices` is a set of vertices
    `edges` is a set of edges
    `heads` is a mapping from edges to vertices mapping
       each edge to its head
    `tails` is a mapping from edges to vertices mapping
       each edge to its tail

    `vertices` and `edges` may contain any hashable Python objects.

    """
    ###########################################################################
    ### IDirectedGraph interface.
    ###########################################################################

    def head(self, edge):
        """
        Return the head (target, destination) of the given edge.

        """
        return self._heads[edge]

    def tail(self, edge):
        """
        Return the tail (source) of the given edge.

        """
        return self._tails[edge]

    def out_edges(self, vertex):
        """
        Return a list of the edges leaving the given vertex.

        """
        return self._out_edges[vertex]

    def in_edges(self, vertex):
        """
        Return a list of the edges entering the given vertex.

        """
        return self._in_edges[vertex]

    @property
    def vertices(self):
        return self._vertices

    @property
    def edges(self):
        return self._edges

    def full_subgraph(self, vertices):
        """
        Return the subgraph of this graph whose vertices
        are the given ones and whose edges are all the edges
        of the original graph between those vertices.

        """
        subgraph_vertices = {v for v in vertices}
        subgraph_edges = {edge
                          for v in subgraph_vertices
                          for edge in self._out_edges[v]
                          if self._heads[edge] in subgraph_vertices}
        subgraph_heads = {edge: self._heads[edge]
                          for edge in subgraph_edges}
        subgraph_tails = {edge: self._tails[edge]
                          for edge in subgraph_edges}
        return DirectedGraph._raw(
            vertices=subgraph_vertices,
            edges=subgraph_edges,
            heads=subgraph_heads,
            tails=subgraph_tails,
        )

    ###########################################################################
    ### DirectedGraph constructors.
    ###########################################################################

    @classmethod
    def _raw(cls, vertices, edges, heads, tails):
        """
        Private constructor for direct construction of
        a DirectedGraph from its consituents.

        """
        self = object.__new__(cls)
        self._vertices = vertices
        self._edges = edges
        self._heads = heads
        self._tails = tails

        # For future use, map each vertex to its outward and inward edges.
        # These could be computed on demand instead of precomputed.
        self._out_edges = collections.defaultdict(set)
        self._in_edges = collections.defaultdict(set)
        for edge in self._edges:
            self._out_edges[self._tails[edge]].add(edge)
            self._in_edges[self._heads[edge]].add(edge)
        return self

    @classmethod
    def from_out_edges(cls, vertices, edge_mapper):
        """
        Create a DirectedGraph from a collection of vertices and
        a mapping giving the vertices that each vertex is connected to.

        """
        vertices = set(vertices)
        edges = set()
        heads = {}
        tails = {}

        # Number the edges arbitrarily.
        edge_identifier = itertools.count()
        for tail in vertices:
            for head in edge_mapper[tail]:
                edge = next(edge_identifier)
                edges.add(edge)
                heads[edge] = head
                tails[edge] = tail

        return cls._raw(
            vertices=vertices,
            edges=edges,
            heads=heads,
            tails=tails,
        )

    @classmethod
    def from_edge_pairs(cls, vertices, edge_pairs):
        """
        Create a DirectedGraph from a collection of vertices
        and a collection of pairs giving links between the vertices.

        """
        vertices = set(vertices)
        edges = set()
        heads = {}
        tails = {}

        # Number the edges arbitrarily.
        edge_identifier = itertools.count()
        for tail, head in edge_pairs:
            edge = next(edge_identifier)
            edges.add(edge)
            heads[edge] = head
            tails[edge] = tail

        return cls._raw(
            vertices=vertices,
            edges=edges,
            heads=heads,
            tails=tails,
        )

    def annotated(self):
        """
        Return an AnnotatedGraph with the same structure
        as this graph.

        """
        annotated_vertices = {
            vertex: AnnotatedVertex(
                id=vertex_id,
                annotation=six.text_type(vertex),
            )
            for vertex_id, vertex in zip(itertools.count(), self.vertices)
        }

        annotated_edges = [
            AnnotatedEdge(
                id=edge_id,
                annotation=six.text_type(edge),
                head=annotated_vertices[self.head(edge)].id,
                tail=annotated_vertices[self.tail(edge)].id,
            )
            for edge_id, edge in zip(itertools.count(), self.edges)
        ]

        return AnnotatedGraph(
            vertices=annotated_vertices.values(),
            edges=annotated_edges,
        )

    def to_dot(self):
        """
        Return a string representing this graph in the DOT format.

        """
        return self.annotated().to_dot()

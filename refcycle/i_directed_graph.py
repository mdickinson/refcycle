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
Abstract base class for the various flavours of directed graph.

"""
import abc
from collections import Container, Iterable, Sized, deque


class IDirectedGraph(Container, Iterable, Sized):
    """
    Abstract base class for directed graphs.

    """
    @abc.abstractproperty
    def vertices(self):
        """
        Return a collection of the vertices of the graph.  The collection
        should support iteration and rapid containment testing.

        """

    @abc.abstractproperty
    def edges(self):
        """
        Return a collection of the edges of the graph.  The collection
        should support iteration and rapid containment testing.

        """

    @abc.abstractmethod
    def head(self, edge):
        """
        Return the head (target, destination) of the given edge.

        """

    @abc.abstractmethod
    def tail(self, edge):
        """
        Return the tail (source) of the given edge.

        """

    @abc.abstractmethod
    def out_edges(self, vertex):
        """
        Return an iterable of the edges leaving the given vertex.

        """

    @abc.abstractmethod
    def in_edges(self, vertex):
        """
        Return an iterable of the edges entering the given vertex.

        """

    @abc.abstractproperty
    def full_subgraph(self, vertices):
        """
        Return the subgraph of this graph whose vertices
        are the given ones and whose edges are all the edges
        of the original graph between those vertices.

        """

    @classmethod
    def vertex_set(cls):
        """
        Return an empty object suitable for storing a set of vertices.

        Usually a plain set will suffice, but for the ObjectGraph we'll use an
        ElementTransformSet instead.

        """
        return set()

    @classmethod
    def vertex_dict(cls):
        """
        Return an empty mapping whose keys are vertices.

        Usually a plain dict is good enough; for the ObjectGraph we'll override
        to use KeyTransformDict instead.

        """
        return dict()

    def __len__(self):
        """
        Number of vertices in the graph.

        """
        return len(self.vertices)

    def __iter__(self):
        """
        Generate objects of graph.

        """
        return iter(self.vertices)

    def __contains__(self, vertex):
        """
        Return True if vertex is a vertex of the graph, else False.

        """
        return vertex in self.vertices

    def __repr__(self):
        return "<{}.{} object of size {} at 0x{:x}>".format(
            self.__module__,
            type(self).__name__,
            len(self),
            id(self),
        )

    def children(self, vertex):
        """
        Return the list of immediate children of the given vertex.

        """
        return [self.head(edge) for edge in self.out_edges(vertex)]

    def parents(self, vertex):
        """
        Return the list of immediate parents of this vertex.

        """
        return [self.tail(edge) for edge in self.in_edges(vertex)]

    def references(self):
        """
        Return (tail, head) pairs for each edge in the
        graph.

        """
        return [
            (tail, head)
            for tail in self.vertices
            for head in self.children(tail)
        ]

    def descendants(self, start, generations=None):
        """
        Return the subgraph of all nodes reachable
        from the given start vertex, including that vertex.

        If specified, the optional `generations` argument specifies how
        many generations to limit to.

        """
        visited = self.vertex_set()
        to_visit = deque([(start, 0)])
        while to_visit:
            vertex, depth = to_visit.popleft()
            visited.add(vertex)
            if generations is None or depth < generations:
                to_visit.extend(
                    (child, depth+1) for child in self.children(vertex)
                    if child not in visited
                )
        return self.full_subgraph(visited)

    def ancestors(self, start, generations=None):
        """
        Return the subgraph of all nodes from which the given vertex is
        reachable, including that vertex.

        If specified, the optional `generations` argument specifies how
        many generations to limit to.

        """
        visited = self.vertex_set()
        to_visit = deque([(start, 0)])
        while to_visit:
            vertex, depth = to_visit.popleft()
            visited.add(vertex)
            if generations is None or depth < generations:
                to_visit.extend(
                    (parent, depth+1) for parent in self.parents(vertex)
                    if parent not in visited
                )
        return self.full_subgraph(visited)

    def _component_graph(self):
        """
        Compute the graph of strongly connected components.

        Each strongly connected component is itself represented as a list of
        pairs, giving information not only about the vertices belonging to
        this strongly connected component, but also the edges leading from
        this strongly connected component to other components.

        Each pair is of the form ('EDGE', v) or ('VERTEX', v) for some vertex
        v.  In the first case, that indicates that there's an edge from this
        strongly connected component to the given vertex v (which will belong
        to another component); in the second, it indicates that v is a member
        of this strongly connected component.

        Each component will begin with a vertex (the *root* vertex of the
        strongly connected component); the following edges are edges from that
        vertex.

        Algorithm is based on that described in "Path-based depth-first search
        for strong and biconnected components" by Harold N. Gabow,
        Inf.Process.Lett. 74 (2000) 107--114.

        """
        sccs = []
        stack = []
        boundaries = []
        identified = self.vertex_set()
        index = self.vertex_dict()
        to_do = []

        def visit_vertex(v):
            index[v] = len(stack)
            stack.append(('VERTEX', v))
            boundaries.append(index[v])
            to_do.append((leave_vertex, v))
            to_do.extend((visit_edge, w) for w in self.children(v))

        def visit_edge(v):
            if v in identified:
                stack.append(('EDGE', v))
            elif v in index:
                while index[v] < boundaries[-1]:
                    boundaries.pop()
            else:
                to_do.append((visit_vertex, v))

        def leave_vertex(v):
            if boundaries[-1] == index[v]:
                root = boundaries.pop()
                scc = stack[root:]
                del stack[root:]
                for item_type, w in scc:
                    if item_type == 'VERTEX':
                        identified.add(w)
                        del index[w]
                sccs.append(scc)
                stack.append(('EDGE', v))

        # Visit every vertex of the graph.
        for v in self.vertices:
            if v not in identified:
                to_do.append((visit_vertex, v))
                while to_do:
                    operation, v = to_do.pop()
                    operation(v)
                stack.pop()

        return sccs

    def source_components(self):
        """
        Return the strongly connected components not reachable from any other
        component.  Any component in the graph is reachable from one of these.

        """
        raw_sccs = self._component_graph()

        # Construct a dictionary mapping each vertex to the root of its scc.
        vertex_to_root = self.vertex_dict()

        # And keep track of which SCCs have incoming edges.
        non_sources = self.vertex_set()

        # Build maps from vertices to roots, and identify the sccs that *are*
        # reachable from other components.
        for scc in raw_sccs:
            root = scc[0][1]
            for item_type, w in scc:
                if item_type == 'VERTEX':
                    vertex_to_root[w] = root
                elif item_type == 'EDGE':
                    non_sources.add(vertex_to_root[w])

        sccs = []
        for raw_scc in raw_sccs:
            root = raw_scc[0][1]
            if root not in non_sources:
                sccs.append([v for vtype, v in raw_scc if vtype == 'VERTEX'])

        return [self.full_subgraph(scc) for scc in sccs]

    def strongly_connected_components(self):
        """
        Return list of strongly connected components of this graph.

        Returns a list of subgraphs.

        Algorithm is based on that described in "Path-based depth-first search
        for strong and biconnected components" by Harold N. Gabow,
        Inf.Process.Lett. 74 (2000) 107--114.

        """
        raw_sccs = self._component_graph()

        sccs = []
        for raw_scc in raw_sccs:
            sccs.append([v for vtype, v in raw_scc if vtype == 'VERTEX'])

        return [self.full_subgraph(scc) for scc in sccs]

    def __sub__(self, other):
        """
        Return the full subgraph containing all vertices
        in self except those in other.

        """
        difference = [v for v in self.vertices if v not in other.vertices]
        return self.full_subgraph(difference)

    def __and__(self, other):
        """
        Return the intersection of the two graphs.

        Returns the full subgraph of self on the intersection
        of self.vertices and other.vertices.  Note that this operation
        is not necessarily symmetric, though in the common case where
        both self and other are already full subgraphs of a larger
        graph, it will be.

        """
        intersection = [v for v in self.vertices if v in other.vertices]
        return self.full_subgraph(intersection)

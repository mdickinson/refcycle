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
Base class for the various flavours of directed graph.

"""
import six


class cached_property(object):
    def __init__(self, func):
        self._func = func
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__

    def __get__(self, obj, type):
        result = self._func(obj)
        obj.__dict__[self.__name__] = result
        return result


class IDirectedGraph(object):
    """
    Abstract base class for directed graphs.

    """
    @cached_property
    def _object_map(self):
        id = self.id_map
        return {id(obj): obj for obj in self.vertices}

    def __len__(self):
        """
        Number of vertices in the graph.

        """
        return len(self._object_map)

    def __iter__(self):
        """
        Generate objects of graph.

        """
        return six.itervalues(self._object_map)

    def __contains__(self, value):
        """
        Return True if value represents an object of the graph,
        else False.

        """
        return self.id_map(value) in self._object_map

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
        from the given start vertex.

        If specified, the optional `generations` arguments specifies how
        many generations to limit to.

        """
        id = self.id_map

        visited = set()
        stack = []
        to_visit = [(start, 0)]
        while to_visit:
            vertex, depth = to_visit.pop()
            if generations is not None and depth > generations:
                continue
            stack.append(vertex)
            visited.add(id(vertex))
            for head in self.children(vertex):
                if id(head) not in visited:
                    to_visit.append((head, depth+1))
        return self.complete_subgraph_on_vertices(stack)

    def ancestors(self, start, generations=None):
        """
        Return the subgraph of all nodes from which the given vertex is
        reachable.

        If specified, the optional `generations` arguments specifies how
        many generations to limit to.

        """
        id = self.id_map

        visited = set()
        stack = []
        to_visit = [(start, 0)]
        while to_visit:
            vertex, depth = to_visit.pop()
            if generations is not None and depth > generations:
                continue
            stack.append(vertex)
            visited.add(id(vertex))
            for head in self.parents(vertex):
                if id(head) not in visited:
                    to_visit.append((head, depth+1))
        return self.complete_subgraph_on_vertices(stack)

    def _component_graph(self):
        """Compute the graph of strongly connected components.

        Returns a list of strongly connected components.

        Each strongly connected component is itself represented as a list of
        pairs, giving information not only about the vertices belonging to
        this strongly connected component, but also the edges leading from
        this strongly connected component to other components.

        Each pair is of the form ('EDGE', v) or ('VERTEX', v) for some vertex
        v.  In the first case, that indicates that there's an edge from this
        strongly connected component to the given vertex v (which will belong
        to another component); in the second, it indicates that v is a member
        of this strongly connected component.

        Notes
        =====
        Algorithm is based on that described in "Path-based depth-first search
        for strong and biconnected components" by Harold N. Gabow,
        Inf.Process.Lett. 74 (2000) 107--114.

        """
        id = self.id_map

        identified = set()
        stack = []
        index = {}
        boundaries = []
        sccs = []
        to_do = []

        def visit_vertex(v):
            index[id(v)] = len(stack)
            stack.append(('VERTEX', v))
            boundaries.append(index[id(v)])
            to_do.append((leave_vertex, v))
            to_do.extend((visit_edge, w) for w in self.children(v))

        def visit_edge(v):
            if id(v) in identified:
                stack.append(('EDGE', v))
            elif id(v) in index:
                while index[id(v)] < boundaries[-1]:
                    boundaries.pop()
            else:
                to_do.append((visit_vertex, v))

        def leave_vertex(v):
            if boundaries[-1] == index[id(v)]:
                root = boundaries.pop()
                scc = stack[root:]
                del stack[root:]
                for item_type, w in scc:
                    if item_type == 'VERTEX':
                        identified.add(id(w))
                        del index[id(w)]
                sccs.append(scc)
                stack.append(('EDGE', v))

        # Visit every vertex of the graph.
        for v in self.vertices:
            if id(v) not in identified:
                to_do.append((visit_vertex, v))
                while to_do:
                    operation, v = to_do.pop()
                    operation(v)
                stack.pop()

        return sccs

    def strongly_connected_components(self):
        """
        Return list of strongly connected components of this graph.

        Returns a list of subgraphs.

        Notes
        =====
        Algorithm is based on that described in "Path-based depth-first search
        for strong and biconnected components" by Harold N. Gabow,
        Inf.Process.Lett. 74 (2000) 107--114.

        """
        raw_sccs = self._component_graph()

        sccs = []
        for raw_scc in raw_sccs:
            sccs.append([v for vtype, v in raw_scc if vtype == 'VERTEX'])

        return [self.complete_subgraph_on_vertices(scc) for scc in sccs]

    def __sub__(self, other):
        """
        Return the complete subgraph containing all vertices
        in self except those in other.  Assumes that self
        and other share the same `id_map`.

        """
        id = self.id_map

        other_vertices = {id(v) for v in other.vertices}

        difference = []
        for v in self.vertices:
            if id(v) not in other_vertices:
                difference.append(v)

        return self.complete_subgraph_on_vertices(difference)

    def __and__(self, other):
        """
        Return the intersection of the two graphs.

        Returns the complete subgraph of self on the intersection
        of self.vertices and other.vertices.  Note that this operation
        is not necessarily symmetric, though in the common case where
        both self and other are already complete subgraphs of a larger
        graph, it will be.

        Assumes that self and other share the same `id_map`.

        """
        id = self.id_map

        other_vertices = {id(v) for v in other.vertices}

        intersection = []
        for v in self.vertices:
            if id(v) in other_vertices:
                intersection.append(v)

        return self.complete_subgraph_on_vertices(intersection)

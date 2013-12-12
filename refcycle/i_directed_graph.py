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
import abc

from six.moves import map

from refcycle.element_transform_set import ElementTransformSet
from refcycle.key_transform_dict import KeyTransformDict


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
    __metaclass__ = abc.ABCMeta

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

    @abc.abstractproperty
    def complete_subgraph_on_vertices(self, vertices):
        """
        Return the subgraph of this graph whose vertices
        are the given ones and whose edges are all the edges
        of the original graph between those vertices.

        """

    def id_map(self, vertex):
        return vertex

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
        visited = ElementTransformSet(transform=self.id_map)
        stack = []
        to_visit = [(start, 0)]
        while to_visit:
            vertex, depth = to_visit.pop()
            if generations is not None and depth > generations:
                continue
            stack.append(vertex)
            visited.add(vertex)
            to_visit.extend(
                (child, depth+1) for child in self.children(vertex)
                if child not in visited
            )
        return self.complete_subgraph_on_vertices(stack)

    def ancestors(self, start, generations=None):
        """
        Return the subgraph of all nodes from which the given vertex is
        reachable, including that vertex.

        If specified, the optional `generations` argument specifies how
        many generations to limit to.

        """
        visited = ElementTransformSet(transform=self.id_map)
        stack = []
        to_visit = [(start, 0)]
        while to_visit:
            vertex, depth = to_visit.pop()
            if generations is not None and depth > generations:
                continue
            stack.append(vertex)
            visited.add(vertex)
            to_visit.extend(
                (parent, depth+1) for parent in self.parents(vertex)
                if parent not in visited
            )
        return self.complete_subgraph_on_vertices(stack)

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
        sccs = []
        stack = []
        boundaries = []
        identified = ElementTransformSet(transform=self.id_map)
        index = KeyTransformDict(transform=self.id_map)

        for v in self.vertices:
            if v not in index:
                to_do = [('VISIT', v)]
                while to_do:
                    operation_type, v = to_do.pop()
                    if operation_type == 'VISIT':
                        index[v] = len(stack)
                        # Append the actual object.
                        stack.append(v)
                        boundaries.append(index[v])
                        to_do.append(('POSTVISIT', v))
                        to_do.extend(('EDGE', w) for w in self.children(v))
                    elif operation_type == 'EDGE':
                        if v not in index:
                            to_do.append(('VISIT', v))
                        elif v not in identified:
                            while index[v] < boundaries[-1]:
                                boundaries.pop()
                    else:
                        # operation_type == 'POSTVISIT'
                        if boundaries[-1] == index[v]:
                            boundaries.pop()
                            scc = stack[index[v]:]
                            del stack[index[v]:]
                            identified.update(scc)
                            sccs.append(scc)

        return list(map(self.complete_subgraph_on_vertices, sccs))

    def __sub__(self, other):
        """
        Return the complete subgraph containing all vertices
        in self except those in other.

        """
        difference = [v for v in self.vertices if v not in other.vertices]
        return self.complete_subgraph_on_vertices(difference)

    def __and__(self, other):
        """
        Return the intersection of the two graphs.

        Returns the complete subgraph of self on the intersection
        of self.vertices and other.vertices.  Note that this operation
        is not necessarily symmetric, though in the common case where
        both self and other are already complete subgraphs of a larger
        graph, it will be.

        """
        intersection = [v for v in self.vertices if v in other.vertices]
        return self.complete_subgraph_on_vertices(intersection)

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
Tools to analyze the Python object graph and find reference cycles.

"""
import gc
import itertools

import six

from refcycle.annotations import object_annotation, annotated_references
from refcycle.annotated_graph import (
    AnnotatedEdge,
    AnnotatedGraph,
    AnnotatedVertex,
)
from refcycle.element_transform_set import ElementTransformSet
from refcycle.key_transform_dict import KeyTransformDict
from refcycle.i_directed_graph import IDirectedGraph


class ObjectGraph(IDirectedGraph):
    """Directed graph representing a collection of Python objects and the
    references between them.

    An ObjectGraph can be constructed directly from an existing iterable
    collection of objects::

        >>> from refcycle import ObjectGraph
        >>> inner = [1, 2, 3]
        >>> outer = [inner] * 3
        >>> graph = ObjectGraph([outer, inner])
        >>> graph
        <refcycle.object_graph.ObjectGraph object of size 2 at 0x100470ed0>

    This constructs a graph whose vertices are the two Python objects ``inner``
    and ``outer``.  All references between the given objects are automatically
    added as graph edges.

    The ObjectGraph acts as a container for those objects, much like a set::

        >>> inner in graph
        True
        >>> 2 in graph
        False
        >>> len(graph)
        2
        >>> list(graph)
        [[[1, 2, 3], [1, 2, 3], [1, 2, 3]], [1, 2, 3]]

    We can find the referrers and referents of any particular object in the
    graph using the :meth:`~refcycle.object_graph.ObjectGraph.parents` and
    :meth:`~refcycle.object_graph.ObjectGraph.children` methods.

        >>> graph.children(outer)
        [[1, 2, 3], [1, 2, 3], [1, 2, 3]]

    Here we see ``inner`` occurring three times as a child of ``outer``,
    because there are three distinct references from ``outer`` to ``inner``.

    """
    ###########################################################################
    ### IDirectedGraph interface.
    ###########################################################################

    def head(self, edge):
        """
        Return the head (target, destination) of the given edge.

        """
        return self._head[edge]

    def tail(self, edge):
        """
        Return the tail (source) of the given edge.

        """
        return self._tail[edge]

    def out_edges(self, vertex):
        """
        Return a list of the edges leaving this vertex.

        """
        return self._out_edges[vertex]

    def in_edges(self, vertex):
        """
        Return a list of the edges entering this vertex.

        """
        return self._in_edges[vertex]

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

    def full_subgraph(self, objects):
        """
        Return the subgraph of this graph whose vertices
        are the given ones and whose edges are the edges
        of the original graph between those vertices.

        """
        vertices = ElementTransformSet(transform=id)
        out_edges = KeyTransformDict(transform=id)
        in_edges = KeyTransformDict(transform=id)
        for obj in objects:
            vertices.add(obj)
            out_edges[obj] = []
            in_edges[obj] = []

        edges = set()
        head = {}
        tail = {}

        for referrer in vertices:
            for edge in self._out_edges[referrer]:
                referent = self._head[edge]
                if referent not in vertices:
                    continue
                edges.add(edge)
                tail[edge] = referrer
                head[edge] = referent
                out_edges[referrer].append(edge)
                in_edges[referent].append(edge)

        return ObjectGraph._raw(
            vertices=vertices,
            edges=edges,
            out_edges=out_edges,
            in_edges=in_edges,
            head=head,
            tail=tail,
        )

    ###########################################################################
    ### Set and dict overrides.
    ###########################################################################

    @classmethod
    def vertex_set(cls):
        return ElementTransformSet(transform=id)

    @classmethod
    def vertex_dict(cls):
        return KeyTransformDict(transform=id)

    @classmethod
    def vertex_equal(cls, vertex1, vertex2):
        return vertex1 is vertex2

    ###########################################################################
    ### ObjectGraph constructors.
    ###########################################################################

    @classmethod
    def _raw(cls, vertices, edges, out_edges, in_edges, head, tail):
        """
        Private constructor for direct construction
        of an ObjectGraph from its attributes.

        vertices is the collection of vertices
        out_edges and in_edges map vertices to lists of edges
        head and tail map edges to objects.

        """
        self = object.__new__(cls)
        self._out_edges = out_edges
        self._in_edges = in_edges
        self._head = head
        self._tail = tail
        self._vertices = vertices
        self._edges = edges
        return self

    @classmethod
    def _from_objects(cls, objects):
        """
        Private constructor: create graph from the given Python objects.

        The constructor examines the referents of each given object to build up
        a graph showing the objects and their links.

        """
        vertices = ElementTransformSet(transform=id)
        out_edges = KeyTransformDict(transform=id)
        in_edges = KeyTransformDict(transform=id)
        for obj in objects:
            vertices.add(obj)
            out_edges[obj] = []
            in_edges[obj] = []

        # Edges are identified by simple integers, so
        # we can use plain dictionaries for mapping
        # edges to their heads and tails.
        edge_label = itertools.count()
        edges = set()
        head = {}
        tail = {}

        for referrer in vertices:
            for referent in gc.get_referents(referrer):
                if referent not in vertices:
                    continue
                edge = next(edge_label)
                edges.add(edge)
                tail[edge] = referrer
                head[edge] = referent
                out_edges[referrer].append(edge)
                in_edges[referent].append(edge)

        return cls._raw(
            vertices=vertices,
            edges=edges,
            out_edges=out_edges,
            in_edges=in_edges,
            head=head,
            tail=tail,
        )

    def __new__(cls, objects=()):
        return cls._from_objects(objects)

    ###########################################################################
    ### Annotations.
    ###########################################################################

    def annotated(self):
        """
        Annotate this graph, returning an AnnotatedGraph object
        with the same structure.

        """
        # Build up dictionary of edge annotations.
        edge_annotations = {}
        for edge in self.edges:
            if edge not in edge_annotations:
                # We annotate all edges from a given object at once.
                referrer = self._tail[edge]
                known_refs = annotated_references(referrer)
                for out_edge in self._out_edges[referrer]:
                    referent = self._head[out_edge]
                    if known_refs[referent]:
                        annotation = known_refs[referent].pop()
                    else:
                        annotation = None
                    edge_annotations[out_edge] = annotation

        annotated_vertices = [
            AnnotatedVertex(
                id=id(vertex),
                annotation=object_annotation(vertex),
            )
            for vertex in self.vertices
        ]

        annotated_edges = [
            AnnotatedEdge(
                id=edge,
                annotation=edge_annotations[edge],
                head=id(self._head[edge]),
                tail=id(self._tail[edge]),
            )
            for edge in self.edges
        ]

        return AnnotatedGraph(
            vertices=annotated_vertices,
            edges=annotated_edges,
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
        return self.annotated().export_image(
            filename=filename,
            format=format,
            dot_executable=dot_executable,
        )

    ###########################################################################
    ### JSON serialization.
    ###########################################################################

    def to_json(self):
        """
        Convert to a JSON string.

        """
        return self.annotated().to_json()

    def export_json(self, filename):
        """
        Export graph in JSON form to the given file.

        """
        self.annotated().export_json(filename=filename)

    def to_dot(self):
        """
        Produce a graph in DOT format.

        """
        return self.annotated().to_dot()

    ###########################################################################
    ### Other utility methods.
    ###########################################################################

    def owned_objects(self):
        """
        List of gc-tracked objects owned by this ObjectGraph instance.

        """
        return (
            [
                self,
                self.__dict__,
                self._head,
                self._tail,
                self._out_edges,
                self._out_edges._keys,
                self._out_edges._values,
                self._in_edges,
                self._in_edges._keys,
                self._in_edges._values,
                self._vertices,
                self._vertices._elements,
                self._edges,
            ] +
            list(six.itervalues(self._out_edges)) +
            list(six.itervalues(self._in_edges))
        )

    def find_by_typename(self, typename):
        """
        List of all objects whose type has the given name.
        """
        return self.find_by(lambda obj: type(obj).__name__ == typename)

    def count_by_typename(self):
        """Classify objects by type name.

        Returns a collections.Counter instance mapping type names to the number
        of objects `obj` in this graph for which `type(obj).__name__` matches
        that type name.
        """
        return self.count_by(lambda obj: type(obj).__name__)

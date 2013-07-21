import collections

from refcycle.i_directed_graph import IDirectedGraph


class AnnotatedEdge(object):
    def __new__(cls, id, annotation, head, tail):
        self = object.__new__(cls)
        self.id = id
        self.annotation = annotation
        self.head = head
        self.tail = tail
        return self


class AnnotatedVertex(object):
    def __new__(cls, id, annotation):
        self = object.__new__(cls)
        self.id = id
        self.annotation = annotation
        return self


class AnnotatedGraph(IDirectedGraph):
    ###########################################################################
    ### IDirectedGraph interface.
    ###########################################################################

    def id_map(self, obj):
        return obj.id

    @property
    def vertices(self):
        """
        Return list of vertices of the graph.

        """
        return self._vertices

    def children(self, obj):
        """
        Return a list of direct descendants of the given object.

        """
        return [edge.head for edge in self._out_edges[self.id_map(obj)]]

    def parents(self, obj):
        """
        Return a list of direct ancestors of the given object.

        """
        return [edge.tail for edge in self._in_edges[self.id_map(obj)]]

    def complete_subgraph_on_vertices(self, vertices):
        """
        Return the subgraph of this graph whose vertices
        are the given ones and whose edges are the edges
        of the original graph between those vertices.

        """
        vertex_ids = {self.id_map(vertex) for vertex in vertices}
        edges = [
            edge for edge in self._edges
            if edge.tail.id in vertex_ids
            if edge.head.id in vertex_ids
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
        self._vertices = vertices
        self._edges = edges

        self._out_edges = collections.defaultdict(list)
        self._in_edges = collections.defaultdict(list)
        for edge in self._edges:
            self._out_edges[edge.tail.id].append(edge)
            self._in_edges[edge.head.id].append(edge)

        return self

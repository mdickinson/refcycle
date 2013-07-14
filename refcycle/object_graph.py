"""
Tools to analyze the Python object graph and find reference cycles.

"""
import gc
import json

from refcycle.annotations import object_annotation, annotated_references
from refcycle.directed_graph import DirectedGraph
from refcycle.i_directed_graph import IDirectedGraph


class ObjectGraph(IDirectedGraph):
    ###########################################################################
    ### IDirectedGraph interface.
    ###########################################################################

    id_map = id

    @property
    def vertices(self):
        """
        Return list of vertices of the graph.

        """
        return self._id_to_object.values()

    def children(self, obj):
        """
        Return a list of direct descendants of the given object.

        """
        return [
            self._head[edge]
            for edge in self._out_edges[self.id_map(obj)]
        ]

    def parents(self, obj):
        """
        Return a list of direct ancestors of the given object.

        """
        return [
            self._tail[edge]
            for edge in self._in_edges[self.id_map(obj)]
        ]

    def complete_subgraph_on_vertices(self, vertices):
        """
        Return the subgraph of this graph whose vertices
        are the given ones and whose edges are the edges
        of the original graph between those vertices.

        """
        return ObjectGraph._raw(
            id_to_object={
                self.id_map(v): v
                for v in vertices
            },
            id_digraph=self._id_digraph.complete_subgraph_on_vertices(
                {self.id_map(v) for v in vertices}
            )
        )

    ###########################################################################
    ### ObjectGraph constructors.
    ###########################################################################

    @classmethod
    def _raw(cls, id_to_object, id_digraph):
        """
        Private constructor for direct construction
        of an ObjectGraph from its attributes.

        id_to_object is a mapping from ids to objects
        id_digraph is a DirectedGraph on the underlying ids.

        """
        self = object.__new__(cls)
        self._id_to_object = id_to_object
        self._id_digraph = id_digraph

        # Dictionary mapping each object_id to the list of
        # edges from that object.
        self._out_edges = id_digraph._out_edges

        # Dictionary mapping each object_id to the list of
        # edges coming into that object.
        self._in_edges = id_digraph._in_edges

        # Dictionary mapping each edge to its head (source).
        self._head = {
            edge: id_to_object[id_digraph.heads[edge]]
            for edge in id_digraph.edges
        }

        # Dictionary mapping each edge to its tail (destination).
        self._tail = {
            edge: id_to_object[id_digraph.tails[edge]]
            for edge in id_digraph.edges
        }

        # Dictionary mapping object ids to strings.
        self._object_annotations = {}
        # Dictionary mapping edge ids to strings.
        self._edge_annotations = {}

        return self

    @classmethod
    def _from_objects(cls, objects):
        """
        Private constructor: create graph from the given Python objects.

        The constructor examines the referents of each given object to build up
        a graph showing the objects and their links.

        """
        _id_to_object = {cls.id_map(obj): obj for obj in objects}
        _id_edges = {
            id_obj: [
                id_ref
                for id_ref in map(id, gc.get_referents(_id_to_object[id_obj]))
                if id_ref in _id_to_object
            ]
            for id_obj in _id_to_object
        }
        id_digraph = DirectedGraph.from_out_edges(_id_to_object, _id_edges)

        return cls._raw(
            id_to_object=_id_to_object,
            id_digraph=id_digraph,
        )

    def __new__(cls, objects=()):
        return cls._from_objects(objects)

    ###########################################################################
    ### Annotations.
    ###########################################################################

    def _edge_annotation(self, edge):
        """
        Return an annotation for this edge if available, else None.

        """
        if edge not in self._edge_annotations:
            # We annotate all edges from a given object at once.
            obj = self._tail[edge]
            known_refs = annotated_references(obj)
            for out_edge in self._out_edges[self.id_map(obj)]:
                target = self.id_map(self._head[out_edge])
                target_id = self.id_map(target)
                if known_refs[target_id]:
                    annotation = known_refs[target_id].pop()
                else:
                    annotation = None
                self._edge_annotations[out_edge] = annotation
        return self._edge_annotations.get(edge)

    def _object_annotation(self, obj_id):
        """
        Return an annotation for this object if available, else None.

        """
        if obj_id not in self._object_annotations:
            obj = self._id_to_object[obj_id]
            self._object_annotations[obj_id] = object_annotation(obj)
        return self._object_annotations[obj_id]

    def export_json(self):
        """
        Export as Json.

        """
        digraph = self._id_digraph

        obj = {
            'digraph': {
                'vertices': sorted(digraph.vertices),
                'edges': sorted(digraph.edges),
                'heads': [
                    {
                        'edge': key,
                        'head': value,
                    }
                    for key, value in sorted(digraph.heads.items())
                ],
                'tails': [
                    {
                        'edge': key,
                        'tail': value,
                    }
                    for key, value in sorted(digraph.tails.items())
                ],
            },
            'labels': {
                'object_labels': [
                    {
                        'object': vertex,
                        'label': self._object_annotation(vertex),
                    }
                    for vertex in sorted(digraph.vertices)
                ],
                'edge_labels': [
                    {
                        'edge': edge,
                        'label': self._edge_annotation(edge),
                    }
                    for edge in sorted(digraph.edges)
                ],
            },
        }
        return json.dumps(obj)

    def to_dot(self):
        """
        Produce a graph in DOT format.

        """
        vertex_labels = {
            vertex: self._object_annotation(vertex)
            for vertex in self._id_digraph.vertices
        }
        edge_labels = {
            edge: self._edge_annotation(edge)
            for edge in self._id_digraph.edges
        }
        return self._id_digraph.to_dot(
            vertex_labels=vertex_labels,
            edge_labels=edge_labels,
        )

    def owned_objects(self):
        """
        List of gc-tracked objects owned by this ObjectGraph instance.

        """
        return (
            [
                self,
                self.id_map,
                self.__dict__,
                self._id_to_object,
                self._object_annotations,
                self._edge_annotations,
            ] + self._id_digraph._owned_objects()
        )

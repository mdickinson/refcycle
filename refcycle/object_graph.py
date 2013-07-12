"""
Tools to analyze the Python object graph and find reference cycles.

"""
import gc
import json

from refcycle.annotations import object_annotation, annotated_references
from refcycle.directed_graph import DirectedGraph
from refcycle.i_directed_graph import IDirectedGraph


class ObjectGraph(IDirectedGraph):
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
        # Dictionary mapping object ids to strings.
        self._object_annotations = {}
        # Dictionary mapping edge ids to strings.
        self._edge_annotations = {}
        self.id_map = id
        return self

    @classmethod
    def _from_objects(cls, objects):
        """
        Private constructor: create graph from the given Python objects.

        The constructor examines the referents of each given object to build up
        a graph showing the objects and their links.

        """
        _id_to_object = {id(obj): obj for obj in objects}
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

    def _edge_annotation(self, edge):
        """
        Return an annotation for this edge if available, else None.

        """
        if edge not in self._edge_annotations:
            # We annotate all edges from a given object at once.
            obj_id = self._id_digraph.tails[edge]
            obj = self._id_to_object[obj_id]
            known_refs = annotated_references(obj)
            for out_edge in self._id_digraph._out_edges[obj_id]:
                target_id = self._id_digraph.heads[out_edge]
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

    def __repr__(self):
        return "<{}.{} object of size {} at 0x{:x}>".format(
            self.__module__,
            type(self).__name__,
            len(self),
            id(self),
        )

    def __len__(self):
        return len(self._id_digraph)

    def __iter__(self):
        for obj_id in self._id_digraph:
            yield self._id_to_object[obj_id]

    def __contains__(self, value):
        return id(value) in self._id_digraph

    def references(self):
        """
        List of all the references (edges) in the graph.

        Each edge takes the form of a pair (referrer, referent).

        """
        id_digraph = self._id_digraph
        return [
            (
                self._id_to_object[id_digraph.tails[id_edge]],
                self._id_to_object[id_digraph.heads[id_edge]],
            )
            for id_edge in id_digraph.edges
        ]

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

    def children(self, obj):
        """
        Return a list of direct descendants of the given object.

        """
        return [
            self._id_to_object[ref_id]
            for ref_id in self._id_digraph.children(id(obj))
        ]

    def parents(self, obj):
        """
        Return a list of direct ancestors of the given object.

        """
        return [
            self._id_to_object[ref_id]
            for ref_id in self._id_digraph.parents(id(obj))
        ]

    @property
    def vertices(self):
        return [self._id_to_object[obj_id] for obj_id in self._id_digraph]

    def complete_subgraph_on_vertices(self, vertices):
        """
        Return the subgraph of this graph whose vertices
        are the given ones and whose edges are the edges
        of the original graph between those vertices.

        """
        return ObjectGraph._raw(
            id_to_object=self._id_to_object,
            id_digraph=self._id_digraph.complete_subgraph_on_vertices(
                {id(v) for v in vertices}
            )
        )

    def __sub__(self, other):
        return ObjectGraph._raw(
            id_to_object=self._id_to_object,
            id_digraph=self._id_digraph - other._id_digraph,
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

"""
Tools to analyze the Python object graph and find reference cycles.

"""
import collections
import gc
import itertools
import json

from refcycle.annotations import object_annotation, annotated_references
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
            out_edges=self._out_edges,
            in_edges=self._in_edges,
            head=self._head,
            tail=self._tail,
        )

    ###########################################################################
    ### ObjectGraph constructors.
    ###########################################################################

    @classmethod
    def _raw(
            cls,
            id_to_object,
            out_edges, in_edges,
            head, tail,
    ):
        """
        Private constructor for direct construction
        of an ObjectGraph from its attributes.

        id_to_object maps object ids to objects
        out_edges and in_edges map object ids to lists of edges
        head and tail map edges to objects.

        """
        self = object.__new__(cls)
        self._id_to_object = id_to_object
        self._out_edges = out_edges
        self._in_edges = in_edges
        self._head = head
        self._tail = tail
        self._object_annotations = {}
        self._edge_annotations = {}
        return self

    @classmethod
    def _from_objects(cls, objects):
        """
        Private constructor: create graph from the given Python objects.

        The constructor examines the referents of each given object to build up
        a graph showing the objects and their links.

        """
        id = cls.id_map

        id_to_object = {id(obj): obj for obj in objects}

        edge_label = itertools.count()
        head = {}
        tail = {}
        out_edges = collections.defaultdict(list)
        in_edges = collections.defaultdict(list)

        for referrer in objects:
            referrer_id = id(referrer)
            for referent in gc.get_referents(referrer):
                referent_id = id(referent)
                if referent_id not in id_to_object:
                    continue
                edge = next(edge_label)
                tail[edge] = referrer
                head[edge] = referent
                out_edges[referrer_id].append(edge)
                in_edges[referent_id].append(edge)

        return cls._raw(
            id_to_object=id_to_object,
            out_edges=out_edges,
            in_edges=in_edges,
            head=head,
            tail=tail,
        )

    def __new__(cls, objects=()):
        return cls._from_objects(objects)

    ###########################################################################
    ### Private methods.
    ###########################################################################

    @property
    def _edges(self):
        """
        Enumerate edge ids of this graph.

        """
        for vertex in self.vertices:
            for edge in self._out_edges[self.id_map(vertex)]:
                yield edge

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
                target_id = self.id_map(self._head[out_edge])
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

    def _format_edge(self, edge_labels, edge):
        label = edge_labels.get(edge)
        if label is not None:
            template = DOT_LABELLED_EDGE_TEMPLATE
        else:
            template = DOT_EDGE_TEMPLATE
        return template.format(
            start=self.id_map(self._tail[edge]),
            stop=self.id_map(self._head[edge]),
            label=label,
        )

    def to_dot(self):
        """
        Produce a graph in DOT format.

        """
        vertex_labels = {
            self.id_map(vertex): self._object_annotation(self.id_map(vertex))
            for vertex in self.vertices
        }
        edge_labels = {
            edge: self._edge_annotation(edge)
            for edge in self._edges
        }

        edges = [self._format_edge(edge_labels, edge) for edge in self._edges]
        vertices = [
            DOT_VERTEX_TEMPLATE.format(
                vertex=self.id_map(vertex),
                label=vertex_labels[self.id_map(vertex)],
            )
            for vertex in self.vertices
        ]

        return DOT_DIGRAPH_TEMPLATE.format(
            edges=''.join(edges),
            vertices=''.join(vertices),
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

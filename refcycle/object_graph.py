"""
Tools to analyze the Python object graph and find reference cycles.

"""
import gc
import types

from refcycle.directed_graph import DirectedGraph


class ObjectGraph(object):
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

    def to_dot(self):
        """
        Produce a graph in DOT format.

        """
        vertex_labels = {
            id_obj: annotate_object(obj)
            for id_obj, obj in self._id_to_object.iteritems()
        }
        edge_labels = {}
        for edge in self._id_digraph.edges:
            tail = self._id_to_object[self._id_digraph.tails[edge]]
            head = self._id_to_object[self._id_digraph.heads[edge]]
            edge_labels[edge] = annotate_edge(tail, head)

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

    def descendants(self, obj):
        """
        Get the collection of all objects reachable from a particular
        id.

        """
        return ObjectGraph._raw(
            id_to_object=self._id_to_object,
            id_digraph=self._id_digraph.descendants(id(obj)),
        )

    def ancestors(self, obj):
        """
        Return the subgraph of ancestors of the given object.

        """
        return ObjectGraph._raw(
            id_to_object=self._id_to_object,
            id_digraph=self._id_digraph.ancestors(id(obj)),
        )

    def strongly_connected_components(self):
        """
        Find nontrivial strongly-connected components.

        """
        return [
            ObjectGraph._raw(id_to_object=self._id_to_object, id_digraph=scc)
            for scc in self._id_digraph.strongly_connected_components()
        ]

    def __sub__(self, other):
        return ObjectGraph._raw(
            id_to_object=self._id_to_object,
            id_digraph=self._id_digraph - other._id_digraph,
        )

    def owned_objects(self):
        """
        List of gc-tracked objects owned by this ObjectGraph instance.

        """
        return ([self, self.__dict__, self._id_to_object] +
                self._id_digraph._owned_objects())


def annotate_object(obj):
    """
    Return a string to be used for GraphViz nodes.  The string
    should be short but as informative as possible.

    """
    if type(obj).__name__ == 'function':
        return "function\\n{}".format(obj.__name__)
    elif isinstance(obj, tuple):
        return "tuple of length {}".format(len(obj))
    elif isinstance(obj, dict):
        return "dict of size {}".format(len(obj))
    elif isinstance(obj, type):
        return "type\\n{}".format(obj.__name__)
    elif isinstance(obj, types.InstanceType):
        return "instance\\n{}".format(obj.__class__.__name__)
    else:
        return type(obj).__name__


def annotate_edge(obj1, obj2):
    """
    Return a string for the edge from obj1 to obj2, or None
    if no suitable annotation can be found.

    """
    if isinstance(obj1, dict):
        for key, value in obj1.iteritems():
            if value is obj2:
                return key if isinstance(key, str) else None

    if (isinstance(obj1, type) and
        hasattr(obj1, '__mro__') and
        obj1.__mro__ is obj2):
        return '__mro__'

    if (isinstance(obj1, types.FunctionType) and
        hasattr(obj1, 'func_closure') and
        obj1.func_closure is obj2):
        return 'func_closure'

    # Nothing special to say.
    return None

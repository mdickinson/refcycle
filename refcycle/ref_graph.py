"""
Tools to analyze the Python object graph and find reference cycles.

"""
import gc
import inspect
import types

from refcycle.directed_graph import DirectedGraph


class RefGraph(object):
    def __init__(self, _objects, _id_digraph):
        # Not intended to be called directly.
        self._objects = _objects
        self._id_digraph = _id_digraph

    def __repr__(self):
        return "<{} object of size {} at 0x{:x}>".format(
            type(self).__name__, len(self), id(self))

    def __len__(self):
        return len(self._id_digraph)

    def __iter__(self):
        for obj_id in self._id_digraph:
            yield self._objects[obj_id]

    def __contains__(self, value):
        return id(value) in self._id_digraph

    def to_dot(self):
        """
        Produce a graph in DOT format.

        """
        vertex_labels = {
            id_obj: annotate_object(obj)
            for id_obj, obj in self._objects.iteritems()
        }
        edge_labels = {}
        for edge in self._id_digraph.edges:
            tail = self._objects[self._id_digraph.tails[edge]]
            head = self._objects[self._id_digraph.heads[edge]]
            edge_labels[edge] = annotate_edge(tail, head)

        return self._id_digraph.to_dot(
            vertex_labels=vertex_labels,
            edge_labels=edge_labels,
        )

    @classmethod
    def from_objects(cls, objects):
        """
        Create a reference graph from the given Python objects.

        """
        _objects = {id(obj): obj for obj in objects}
        _id_vertices = set(_objects.keys())
        _id_edges = {
            id_obj: {
                id_ref
                for id_ref in map(id, gc.get_referents(_objects[id_obj]))
                if id_ref in _id_vertices
            }
            for id_obj in _id_vertices
        }
        _id_digraph = DirectedGraph.from_out_edges(_id_vertices, _id_edges)

        return cls(
            _id_digraph=_id_digraph,
            _objects=_objects,
        )

    def children(self, obj):
        """
        Return a list of direct descendants of the given object.

        """
        return [
            self._objects[ref_id]
            for ref_id in self._id_digraph.children(id(obj))
        ]

    def parents(self, obj):
        """
        Return a list of direct ancestors of the given object.

        """
        return [
            self._objects[ref_id]
            for ref_id in self._id_digraph.parents(id(obj))
        ]

    def descendants(self, obj):
        """
        Get the collection of all objects reachable from a particular
        id.

        """
        return RefGraph(
            _objects=self._objects,
            _id_digraph=self._id_digraph.descendants(id(obj)),
        )

    def ancestors(self, obj):
        """
        Return the subgraph of ancestors of the given object.

        """
        return RefGraph(
            _objects=self._objects,
            _id_digraph=self._id_digraph.ancestors(id(obj)),
        )

    def strongly_connected_components(self):
        """
        Find nontrivial strongly-connected components.

        """
        return [
            RefGraph(_objects=self._objects, _id_digraph=scc)
            for scc in self._id_digraph.strongly_connected_components()
        ]

    @classmethod
    def snapshot(cls):
        """
        Return a reference graph for all the current objects from
        gc.get_objects.

        """
        all_objects = gc.get_objects()
        this_frame = inspect.currentframe()
        # Don't include the current frame, or the list of objects.
        all_objects = [
            obj for obj in all_objects
            if obj is not this_frame
            if obj is not all_objects
        ]
        del this_frame
        return cls.from_objects(all_objects)

    def __sub__(self, other):
        return RefGraph(
            _objects=self._objects,
            _id_digraph=self._id_digraph - other._id_digraph,
        )

    def owned_objects(self):
        """
        List of gc-tracked objects owned by this RefGraph instance.

        """
        return ([self, self.__dict__, self._objects] +
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


def dump_object(obj):
    """
    Return a suitable representation of an object.

    """
    try:
        str_obj = str(obj)
    except NotImplementedError:
        str_obj = "Not Implemented"
    except AttributeError:
        str_obj = "Attribute error"

    if len(str_obj) > 100:
        str_obj = str_obj[:98] + '...'
    return "object {} of type {!r}: {}".format(
        id(obj),
        type(obj).__name__,
        str_obj,
    )

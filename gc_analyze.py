"""
Tools to analyze the Python object graph and find reference cycles.

"""
import collections
import gc
import inspect
import itertools


class DirectedGraph(object):
    def __init__(self, vertices, edges):
        """
        Object representing a directed graph.

        `vertices` is a collection of vertices.

        `edges` is a mapping that maps each vertex to the collection
            of targets of that vertex.

        """
        self.vertices = vertices
        self.edges = edges

        # Create backedges.  (XXX: do this lazily, on demand.)
        self.backedges = collections.defaultdict(list)
        for tail in self.vertices:
            for head in self.edges[tail]:
                self.backedges[head].append(tail)

    def __len__(self):
        """
        Length is implemented as the number of vertices.

        """
        return len(self.vertices)

    def __contains__(self, vertex):
        """
        Return True if the given vertex is a vertex of the graph.

        """
        return vertex in self.vertices

    def __iter__(self):
        """
        Iterate over the vertices of this graph.

        """
        return iter(self.vertices)

    def complete_subgraph_on_vertices(self, vertices):
        """
        Return the subgraph of this graph whose vertices
        are the given ones and whose edges are all the edges
        of the original graph between those vertices.

        """
        edges = {}
        for v in vertices:
            edges[v] = {w for w in self.edges[v] if w in vertices}
        return DirectedGraph(vertices, edges)

    def dfs_ordering(self):
        """
        Return the list of vertices and edges in the order
        that they're encountered during a depth-first search.

        """
        def dfs_recursive(v):
            visited.add(v)
            vertices.append(v)
            for w in self.edges[v]:
                edges.append((v, w))
                if w not in visited:
                    dfs_recursive(w)

        visited = set()
        vertices = []
        edges = []
        for v in self.vertices:
            if v not in visited:
                dfs_recursive(v)
        return vertices, edges

    def children(self, start):
        return self.edges[start]

    def parents(self, start):
        return self.backedges[start]

    def descendants(self, start):
        """
        Return the subgraph of all nodes reachable
        from the given start vertex.

        """
        def dfs_recursive(v):
            visited.add(v)
            yield v

            for w in self.edges[v]:
                if w not in visited:
                    for node in dfs_recursive(w):
                        yield node
                    dfs_recursive(w)

        visited = set()
        vertices = {node for node in dfs_recursive(start)}
        return self.complete_subgraph_on_vertices(vertices)

    def ancestors(self, start):
        """
        Return the subgraph of all nodes from which the
        given vertex is reachable.

        """
        def dfs_recursive(v):
            visited.add(v)
            yield v

            for w in self.backedges[v]:
                if w not in visited:
                    for node in dfs_recursive(w):
                        yield node
                    dfs_recursive(w)

        visited = set()
        vertices = {node for node in dfs_recursive(start)}
        return self.complete_subgraph_on_vertices(vertices)

    def strongly_connected_components(self):
        """
        Iterator that produces the strongly-connected components of
        this graph.

        """
        # Implementation follows Tarjan's algorithm.

        def strongconnect(v):
            index[v] = lowlink[v] = next(indices)
            stack.append(v)

            # Depth-first search over the children of v.
            for w in self.edges[v]:
                if w not in index:
                    for scc in strongconnect(w):
                        yield scc
                    lowlink[v] = min(lowlink[v], lowlink[w])
                elif w in stack:
                    lowlink[v] = min(lowlink[v], lowlink[w])

            # v is the root of a strongly-connected component;
            # pop it from the stack.
            if lowlink[v] == index[v]:
                scc = set()
                while True:
                    w = stack.pop()
                    scc.add(w)
                    if w == v:
                        break
                yield self.complete_subgraph_on_vertices(scc)

        indices = itertools.count()
        stack = []
        index = {}
        lowlink = {}
        for v in self.vertices:
            if v not in lowlink:
                for scc in strongconnect(v):
                    yield scc

    def to_dot(self, vertex_labels=None):
        """
        Return a string representing this graph in the DOT format used
        by GraphViz.

        Inputs: vertex_labels is a mapping that maps vertices of the
        graph to the labels to be used for the corresponding DOT
        nodes.

        """
        digraph_template = """\
digraph G {{
{edges}\
{vertices}\
}}
"""
        vertex_template = "    {vertex} [label=\"{label}\"];\n"
        edge_template = "    {start} -> {stop};\n"

        edges = [
            edge_template.format(start=vertex, stop=edge)
            for vertex in self.vertices
            for edge in self.edges[vertex]
        ]

        vertices = [
            vertex_template.format(
                vertex=vertex,
                label=vertex_labels[vertex],
            )
            for vertex in self.vertices
        ]

        return digraph_template.format(
            edges=''.join(edges),
            vertices=''.join(vertices),
        )


class RefGraph(object):
    def __init__(self, _objects, _id_digraph):
        # Not intended to be called directly.
        self._objects = _objects
        self._id_digraph = _id_digraph

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
        labels = {
            id_obj: type(obj).__name__
            for id_obj, obj in self._objects.iteritems()
        }

        for id_obj, obj in self._objects.iteritems():
            if type(obj).__name__ == 'function':
                labels[id_obj] = "fn: {}".format(obj.__name__)

        return self._id_digraph.to_dot(vertex_labels=labels)

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
        _id_digraph = DirectedGraph(_id_vertices, _id_edges)

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
        for scc in self._id_digraph.strongly_connected_components():
            if len(scc) > 1:
                yield scc


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


def snapshot_gc(dont_care_ids):
    this_frame = inspect.currentframe()
    all_objs = gc.get_objects()
    live_objects = [
        obj for obj in all_objs
        if id(obj) not in dont_care_ids
        if obj is not dont_care_ids
        if obj is not this_frame
        if obj is not all_objs
    ]
    return RefGraph.from_objects(live_objects)


def refs_generated_by(callable):
    gc.collect()
    dont_care_ids = set(id(obj) for obj in gc.get_objects())

    # Call the callable.
    callable()
    gc.collect()

    # Get references created by the callable.
    return snapshot_gc(dont_care_ids)

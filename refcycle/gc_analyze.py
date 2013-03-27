"""
Tools to analyze the Python object graph and find reference cycles.

"""
import collections
import gc
import inspect
import itertools


class DirectedGraph(object):
    """
    Object representing a directed graph.

    `vertices` is a set of vertices
    `edges` is a set of edges
    `heads` is a mapping from edges to vertices mapping
       each edge to its head
    `tails` is a mapping from edges to vertices mapping
       each edge to its tail

    `vertices` and `edges` may contain any hashable Python objects.

    """
    def __init__(self, vertices, edges, heads, tails):
        """
        This __init__ method is not intended to be called directly
        by users.  Call one of the alternative constructors instead.

        """
        self.vertices = vertices
        self.edges = edges
        self.heads = heads
        self.tails = tails

        # For future use, map each vertex to its outward and inward edges.
        # These could be computed on demand instead of precomputed.
        self._out_edges = collections.defaultdict(set)
        self._in_edges = collections.defaultdict(set)
        for edge in self.edges:
            self._out_edges[self.tails[edge]].add(edge)
            self._in_edges[self.heads[edge]].add(edge)

    def _owned_objects(self):
        """
        gc-tracked objects owned by this graph, including itself.

        """
        objs = [self, self.__dict__, self.vertices, self.edges, self.heads,
               self.tails, self._out_edges, self._in_edges]
        objs += self._out_edges.values()
        objs += self._in_edges.values()
        return objs

    @classmethod
    def from_out_edges(cls, vertices, edge_mapper):
        """
        Create a DirectedGraph from a collection of vertices and
        a mapping giving the vertices that each vertex is connected to.

        """
        vertices = set(vertices)
        edges = set()
        heads = {}
        tails = {}

        # Number the edges arbitrarily.
        edge_identifier = itertools.count()
        for tail in vertices:
            for head in edge_mapper[tail]:
                edge = edge_identifier.next()
                edges.add(edge)
                heads[edge] = head
                tails[edge] = tail

        return cls(
            vertices=vertices,
            edges=edges,
            heads=heads,
            tails=tails,
        )

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

    def __sub__(self, other):
        return self.complete_subgraph_on_vertices(
            self.vertices - other.vertices
        )

    def complete_subgraph_on_vertices(self, vertices):
        """
        Return the subgraph of this graph whose vertices
        are the given ones and whose edges are all the edges
        of the original graph between those vertices.

        """
        if not all(v in self.vertices for v in vertices):
            raise ValueError("Not all vertices are valid.")
        subgraph_vertices = {v for v in vertices}
        subgraph_edges = {edge
                          for v in vertices
                          for edge in self._out_edges[v]
                          if self.heads[edge] in vertices}
        subgraph_heads = {edge: self.heads[edge]
                          for edge in subgraph_edges}
        subgraph_tails = {edge: self.tails[edge]
                          for edge in subgraph_edges}
        return DirectedGraph(
            vertices=subgraph_vertices,
            edges=subgraph_edges,
            heads=subgraph_heads,
            tails=subgraph_tails,
        )

    def dfs_ordering(self):
        """
        Return the list of vertices and edges in the order
        that they're encountered during a depth-first search.

        """
        def dfs_recursive(v):
            visited.add(v)
            vertices.append(v)
            for edge in self._out_edges[v]:
                w = self.tails[edge]
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
        return [self.heads[edge] for edge in self._out_edges[start]]

    def parents(self, start):
        return [self.tails[edge] for edge in self._in_edges[start]]

    def descendants(self, start):
        """
        Return the subgraph of all nodes reachable
        from the given start vertex.

        """
        def dfs_recursive(v):
            visited.add(v)
            yield v

            for edge in self._out_edges[v]:
                w = self.heads[edge]
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

            for edge in self._in_edges[v]:
                w = self.tails[edge]
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
            for edge in self._out_edges[v]:
                w = self.heads[edge]
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

    def to_dot(self, vertex_labels=None, edge_labels=None):
        """
        Return a string representing this graph in the DOT format used
        by GraphViz.

        Inputs: vertex_labels is a mapping that maps vertices of the
        graph to the labels to be used for the corresponding DOT
        nodes.

        Similarly, edge_labels maps edges to labels.

        """
        digraph_template = """\
digraph G {{
{edges}\
{vertices}\
}}
"""
        vertex_template = "    {vertex} [label=\"{label}\"];\n"
        edge_template = "    {start} -> {stop};\n"
        labelled_edge_template = "    {start} -> {stop} [label=\"{label}\"];\n"

        if vertex_labels is None:
            vertex_labels = {vertex: vertex for vertex in self.vertices}

        if edge_labels is None:
            edge_labels = {}

        def format_edge(edge):
            label = edge_labels.get(edge)
            if label is not None:
                return labelled_edge_template.format(
                    start=self.tails[edge],
                    stop=self.heads[edge],
                    label=label,
                )
            else:
                return edge_template.format(
                    start=self.tails[edge],
                    stop=self.heads[edge],
                )

        edges = [format_edge(edge) for edge in self.edges]
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
                return str(key)


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

"""
A 'DirectedGraph' is an object representing a simple directed graph.

A directed graph consists of:

  - a collection of vertices
  - a collection of edges
  - a mapping 'heads' from edges to vertices
  - a mapping 'tails' from edges to vertices

This setup allows for self-edges, and multiple edges between a pair of
vertices.  Since we want to use these directed graphs to represent references
between Python objects, both these capabilities are necessary.

"""
import collections
import itertools

from refcycle.i_directed_graph import IDirectedGraph


class DirectedGraph(IDirectedGraph):
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
        self.id_map = lambda x: x

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
                edge = next(edge_identifier)
                edges.add(edge)
                heads[edge] = head
                tails[edge] = tail

        return cls(
            vertices=vertices,
            edges=edges,
            heads=heads,
            tails=tails,
        )

    @classmethod
    def from_edge_pairs(cls, vertices, edge_pairs):
        """
        Create a DirectedGraph from a collection of vertices
        and a collection of pairs giving links between the vertices.

        """
        vertices = set(vertices)
        edges = set()
        heads = {}
        tails = {}

        # Number the edges arbitrarily.
        edge_identifier = itertools.count()
        for tail, head in edge_pairs:
            edge = next(edge_identifier)
            edges.add(edge)
            heads[edge] = head
            tails[edge] = tail

        return cls(
            vertices=vertices,
            edges=edges,
            heads=heads,
            tails=tails,
        )

    def _owned_objects(self):
        """
        gc-tracked objects owned by this graph, including itself.

        """
        objs = [self, self.__dict__, self.vertices, self.edges, self.heads,
                self.tails, self._out_edges, self._in_edges]
        objs += self._out_edges.values()
        objs += self._in_edges.values()
        return objs

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

    def children(self, start):
        """
        Return the list of immediate children of this vertex.

        """
        return [self.heads[edge] for edge in self._out_edges[start]]

    def parents(self, start):
        """
        Return the list of immediate parents of this vertex.

        """
        return [self.tails[edge] for edge in self._in_edges[start]]

    def descendants(self, start):
        """
        Return the subgraph of all nodes reachable
        from the given start vertex.

        """
        visited = set()
        to_visit = [start]
        while to_visit:
            vertex = to_visit.pop()
            visited.add(vertex)
            for edge in self._out_edges[vertex]:
                head = self.heads[edge]
                if head not in visited:
                    to_visit.append(head)
        return self.complete_subgraph_on_vertices(visited)

    def ancestors(self, start):
        """
        Return the subgraph of all nodes from which the
        given vertex is reachable.

        """
        visited = set()
        to_visit = [start]
        while to_visit:
            vertex = to_visit.pop()
            visited.add(vertex)
            for edge in self._in_edges[vertex]:
                tail = self.tails[edge]
                if tail not in visited:
                    to_visit.append(tail)
        return self.complete_subgraph_on_vertices(visited)

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

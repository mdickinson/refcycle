class cached_property(object):
    def __init__(self, func):
        self._func = func
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__

    def __get__(self, obj, type):
        result = self._func(obj)
        obj.__dict__[self.__name__] = result
        return result


class IDirectedGraph(object):
    """
    Abstract base class for directed graphs.

    """
    @cached_property
    def _object_map(self):
        id = self.id_map
        return {id(obj): obj for obj in self.vertices}

    def __len__(self):
        """
        Number of vertices in the graph.

        """
        return len(self._object_map)

    def __iter__(self):
        """
        Generate objects of graph.

        """
        return self._object_map.itervalues()

    def __contains__(self, value):
        """
        Return True if value represents an object of the graph,
        else False.

        """
        return self.id_map(value) in self._object_map

    def __repr__(self):
        return "<{}.{} object of size {} at 0x{:x}>".format(
            self.__module__,
            type(self).__name__,
            len(self),
            id(self),
        )

    def children(self, vertex):
        """
        Return the list of immediate children of the given vertex.

        """
        return [self.head(edge) for edge in self.out_edges(vertex)]

    def parents(self, vertex):
        """
        Return the list of immediate parents of this vertex.

        """
        return [self.tail(edge) for edge in self.in_edges(vertex)]

    def references(self):
        """
        Return (tail, head) pairs for each edge in the
        graph.

        """
        return [
            (tail, head)
            for tail in self.vertices
            for head in self.children(tail)
        ]

    def descendants(self, start, generations=None):
        """
        Return the subgraph of all nodes reachable
        from the given start vertex.

        If specified, the optional `generations` arguments specifies how
        many generations to limit to.

        """
        id = self.id_map

        visited = set()
        stack = []
        to_visit = [(start, 0)]
        while to_visit:
            vertex, depth = to_visit.pop()
            if generations is not None and depth > generations:
                continue
            stack.append(vertex)
            visited.add(id(vertex))
            for head in self.children(vertex):
                if id(head) not in visited:
                    to_visit.append((head, depth+1))
        return self.complete_subgraph_on_vertices(stack)

    def ancestors(self, start, generations=None):
        """
        Return the subgraph of all nodes from which the given vertex is
        reachable.

        If specified, the optional `generations` arguments specifies how
        many generations to limit to.

        """
        id = self.id_map

        visited = set()
        stack = []
        to_visit = [(start, 0)]
        while to_visit:
            vertex, depth = to_visit.pop()
            if generations is not None and depth > generations:
                continue
            stack.append(vertex)
            visited.add(id(vertex))
            for head in self.parents(vertex):
                if id(head) not in visited:
                    to_visit.append((head, depth+1))
        return self.complete_subgraph_on_vertices(stack)

    def strongly_connected_components(self):
        """
        Return list of strongly connected components of this graph.

        Returns a list of subgraphs.

        Notes
        =====
        Algorithm is based on that described in "Path-based depth-first search
        for strong and biconnected components" by Harold N. Gabow,
        Inf.Process.Lett. 74 (2000) 107--114.

        """
        id = self.id_map

        sccs = []
        identified = set()
        stack = []
        index = {}
        boundaries = []

        for v in self.vertices:
            id_v = id(v)  # Hashable version of v.
            if id_v not in index:
                to_do = [('VISIT', id_v, v)]
                while to_do:
                    operation_type, id_v, v = to_do.pop()
                    if operation_type == 'VISIT':
                        index[id_v] = len(stack)
                        # Append the actual object.
                        stack.append(v)
                        boundaries.append(index[id_v])
                        to_do.append(('POSTVISIT', id_v, v))
                        # The reversal below keeps the search order identical
                        # to that of the recursive version.
                        to_do.extend(reversed([('EDGE', id(w), w)
                                               for w in self.children(v)]))
                    elif operation_type == 'EDGE':
                        if id_v not in index:
                            to_do.append(('VISIT', id_v, v))
                        elif id_v not in identified:
                            while index[id_v] < boundaries[-1]:
                                boundaries.pop()
                    else:
                        # operation_type == 'POSTVISIT'
                        if boundaries[-1] == index[id_v]:
                            boundaries.pop()
                            scc = stack[index[id_v]:]
                            del stack[index[id_v]:]
                            for w in scc:
                                identified.add(id(w))
                            sccs.append(scc)

        return map(self.complete_subgraph_on_vertices, sccs)

    def __sub__(self, other):
        """
        Return the complete subgraph containing all vertices
        in self except those in other.  Assumes that self
        and other share the same `id_map`.

        """
        id = self.id_map

        other_vertices = {id(v) for v in other.vertices}

        difference = []
        for v in self.vertices:
            if id(v) not in other_vertices:
                difference.append(v)

        return self.complete_subgraph_on_vertices(difference)

    def __and__(self, other):
        """
        Return the intersection of the two graphs.

        Returns the complete subgraph of self on the intersection
        of self.vertices and other.vertices.  Note that this operation
        is not necessarily symmetric, though in the common case where
        both self and other are already complete subgraphs of a larger
        graph, it will be.

        Assumes that self and other share the same `id_map`.

        """
        id = self.id_map

        other_vertices = {id(v) for v in other.vertices}

        intersection = []
        for v in self.vertices:
            if id(v) in other_vertices:
                intersection.append(v)

        return self.complete_subgraph_on_vertices(intersection)

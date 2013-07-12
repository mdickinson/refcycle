class IDirectedGraph(object):
    """
    Abstract base class for directed graphs.

    """
    def strongly_connected_components(self):
        """
        Return list of strongly connected components of this graph.

        Returns a list of subgraphs.

        """
        # Based on "Path-based depth-first search for strong and biconnected
        # components" by Harold N. Gabow, Inf.Process.Lett. 74 (2000) 107--114.
        sccs = []
        identified = set()
        stack = []
        index = {}
        boundaries = []

        id = self.id_map

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

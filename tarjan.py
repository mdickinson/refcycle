# Implementation of Tarjan's algorithm, following Wikipedia.
import itertools


def tarjan(vertices, neighbours):
    """
    Inputs:

    vertices: sequence of vertices of the graph.  Vertices should be hashable.

    next: function which when applied to a vertex gives the neighbours of that
        vertex.

    root: root vertex

    Finds strongly connected components reachable from the given vertex.

    """
    def strongconnect(v):
        index[v] = lowlink[v] = next(indices)
        stack.append(v)

        for w in neighbours(v):
            if w not in index:
                for scc in strongconnect(w):
                    yield scc
                lowlink[v] = min(lowlink[v], lowlink[w])
            elif w in stack:
                lowlink[v] = min(lowlink[v], lowlink[w])

        if lowlink[v] == index[v]:
            scc = set()
            while True:
                w = stack.pop()
                scc.add(w)
                if w == v:
                    break

            yield scc

    indices = itertools.count()
    stack = []
    index = {}
    lowlink = {}
    for v in vertices:
        if v not in lowlink:
            for scc in strongconnect(v):
                yield scc

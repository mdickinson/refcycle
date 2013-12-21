import refcycle
import gc
gc.disable()
gc.collect()

class A(object):
    pass

a = A()
b = A()
a.foo = b
b.foo = a
del a, b, A

graph = refcycle.garbage()
graph.export_image('garbage.svg')

sccs = graph.strongly_connected_components()
sccs
sccs.sort(key=len)
sccs[-1].export_image('scc1.svg')
sccs[-2].export_image('scc2.svg')

print graph.source_components()

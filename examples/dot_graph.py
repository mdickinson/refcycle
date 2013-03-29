import gc

from refcycle import RefGraph

gc.disable()
gc.set_debug(gc.DEBUG_SAVEALL)


class A(object):
    pass


def create_cycles():
    a, b, c = A(), A(), A()
    a.foo = b
    b.foo = a
    a.bar = c


gc.collect()
create_cycles()
count = gc.collect()
objects = gc.garbage[-count:]

graph = RefGraph.from_objects(objects)
print graph.to_dot()

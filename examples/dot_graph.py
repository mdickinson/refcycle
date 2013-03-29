from refcycle import cycles_created_by


class A(object):
    pass


def create_cycles():
    a, b, c = A(), A(), A()
    a.foo = b
    b.foo = a
    a.bar = c


graph = cycles_created_by(create_cycles)
print graph.to_dot()

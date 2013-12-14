import gc
import refcycle
gc.disable()
gc.collect()

# Create some cyclic garbage.
a = ["A"]
b = ["B"]
a.append(b)
b.append(a)
del a, b

# Collect it and dump in GraphViz format.
graph = refcycle.garbage()
with open('readme_example1.gv', 'w') as f:
    f.write(graph.to_dot())

# Now if you have 'dot' from GraphViz installed, you can execute the
# command:
#    dot -Tpng readme_example1.gv -o readme_example1.png
# To obtain an output PNG file.

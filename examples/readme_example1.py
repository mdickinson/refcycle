import gc
import refcycle
import subprocess

gc.disable()
gc.collect()

# Create some cyclic garbage.
a = ["A"]
b = ["B"]
a.append(b)
b.append(a)
del a, b

# Collect it and dump in Graphviz format.
graph = refcycle.garbage()
with open('readme_example1.gv', 'w') as f:
    f.write(graph.to_dot())

# If you have dot installed, the following creates a PNG image.
cmd = ['dot', '-Tpng', 'readme_example1.gv', '-o', 'readme_example1.png']
subprocess.check_call(cmd)

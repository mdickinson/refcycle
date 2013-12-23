import refcycle
a = [["hello", "world"], 37]
graph = refcycle.objects_reachable_from(a)
graph
graph.export_image('example.svg')
graph.export_image('example.pdf')

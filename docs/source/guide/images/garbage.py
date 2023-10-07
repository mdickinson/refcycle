# Copyright 2013-2023 Mark Dickinson
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import gc

import refcycle

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
graph.export_image("garbage.svg")
graph.export_image("garbage.pdf")

sccs = graph.strongly_connected_components()
sccs
sccs.sort(key=len)
sccs[-1].export_image("scc1.svg")
sccs[-1].export_image("scc1.pdf")
sccs[-2].export_image("scc2.svg")
sccs[-2].export_image("scc2.pdf")

print(graph.source_components())

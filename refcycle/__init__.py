# Copyright 2013 Mark Dickinson
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

from refcycle.creators import (
    cycles_created_by,
    garbage,
    objects_reachable_from,
    snapshot,
)
from refcycle.annotated_graph import AnnotatedGraph
from refcycle.i_directed_graph import IDirectedGraph
from refcycle.object_graph import ObjectGraph
from refcycle.version import __version__

__all__ = [
    'AnnotatedGraph', 'IDirectedGraph', 'ObjectGraph',
    'cycles_created_by', 'garbage', 'objects_reachable_from', 'snapshot',
    'key_cycles',
    '__version__',
]


def _is_orphan(scc, graph):
    """
    Return False iff the given scc is reachable from elsewhere.

    """
    return all(p in scc for v in scc for p in graph.parents(v))


def key_cycles():
    """
    Collect cyclic garbage, and return the strongly connected
    components that were keeping the garbage alive.

    """
    graph = garbage()
    sccs = graph.strongly_connected_components()
    return [scc for scc in sccs if _is_orphan(scc, graph)]

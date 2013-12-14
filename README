The refcycle package provides support for creating, analysing, and visualising
graphs of Python objects and their references.  Its main intended use is for
finding reference cycles amongst Python objects.

Quick tour
----------

Begin by importing ``refcycle`` and turning off the cyclic garbage collector so
that it doesn't interfere with the examples below.

    >>> import refcycle
    >>> import gc; gc.disable()

Now let's create some cyclic garbage in Python::

    >>> a = ['A']
    >>> b = ['B']
    >>> a.append(b)
    >>> b.append(a)
    >>> del a, b

At this point the two lists created as ``a`` and ``b`` are garbage, but won't
be collected by CPython's reference-count based garbage collection because they
each have a positive reference count.  We can use refcycle to capture that garbage.

    >>> import refcycle
    >>> graph = refcycle.garbage()
    >>> graph
    <refcycle.object_graph.ObjectGraph object of size 2 at 0x10047b350>

The ``garbage`` function returns an ``ObjectGraph`` instance, which captures
the objects and the connections between them.  A convenient way to get a description
is to use the `to_dot` method on the graph::

    >>> print graph.to_dot()
    digraph G {
        4299561656 -> 4299641776 [label="item[1]"];
        4299641776 -> 4299561656 [label="item[1]"];
        4299561656 [label="list[2]"];
        4299641776 [label="list[2]"];
    }

This outputs a string in the .dot format used by GraphViz: it can be saved to a
file and processed by GraphViz to produce a visualization of the graph.



Getting refcycle
----------------

The refcycle project lives on GitHub, at https://github.com/mdickinson/refcycle.


License information
-------------------

The refcycle package is copyright (c) 2013 Mark Dickinson.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

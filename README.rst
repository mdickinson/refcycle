
The refcycle package provides support for creating, analysing, and visualising
graphs of Python objects and the references between them.  Its main intended
use is for finding reference cycles amongst Python objects.


Features
--------

- An `ObjectGraph`_ class representing a collection of objects and references.
- Computation of strongly-connected components of the object graph.
- Ability to export to JSON and reimport later for offline analysis.
- Integration with `Graphviz`_ for exporting images.
- Supports Python 2 and Python 3 (CPython only).


Documentation
-------------

Up-to-date documentation can be found on "Read the Docs", at
http://refcycle.readthedocs.org.


Getting refcycle
----------------

The refcycle project lives on GitHub, at
https://github.com/mdickinson/refcycle.  You can download a snapshot of the
latest development version from there:

- https://github.com/mdickinson/refcycle/archive/master.zip
- https://github.com/mdickinson/refcycle/archive/master.tar.gz

After downloading, unpack the archive, and do::

   cd refcycle-master
   python setup.py install


License
-------

The refcycle package is copyright (c) 2013 Mark Dickinson.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use
this file except in compliance with the License.  You may obtain a copy of the
License at http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
CONDITIONS OF ANY KIND, either express or implied.  See the License for the
specific language governing permissions and limitations under the License.


.. _Graphviz: http://www.graphviz.org
.. _ObjectGraph: http://refcycle.readthedocs.org/en/latest/object_graph.html#refcycle.object_graph.ObjectGraph

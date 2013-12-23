Exploring currently live objects
--------------------------------

The |snapshot| function lets you take a snapshot of the current state of the
Python interpreter, returning a graph of all *tracked* objects and the
references between them.  This can be useful for finding out what's
keeping objects alive.

.. note::
   Simple objects like integers and strings are not tracked by the cyclic
   garbage collector, so they won't show up in the graph returned by
   |snapshot|.

Here's a worked example.  We start with a simple asynchronous worker::

    def worker(jobs_queue, results_queue):
        while True:
            job = jobs_queue.get()
            result = job()
            results_queue.put(result)

It listens for incoming jobs on a queue, performs the computation represented
by each job, and puts the result on another results queue.  We'll start it
running on a separate thread like this::

    try:
        from queue import Queue  # Works in Python 3.
    except ImportError:
        from Queue import Queue  # Python 2 fallback.
    import threading

    jobs_queue, results_queue = Queue(), Queue()
    t = threading.Thread(target=worker, args=(jobs_queue, results_queue))
    t.daemon = True
    t.start()

Now we create some computations, feed them to the worker, and wait for and
print the results::

    class SomeComputation(object):
        def __init__(self, value):
            self.value = value

        def compute(self):
            return self.value**2

    def do_some_computations(jobs_queue, results_queue):
        computations = [SomeComputation(n) for n in [11, 15, 17]]
        for computation in computations:
            jobs_queue.put(computation.compute)
        for computation in computations:
            print(results_queue.get())

    do_some_computations(jobs_queue, results_queue)

So far, so good.  But now we notice that for some reason, after the
``do_some_computation`` call, there's still an instance of ``SomeComputation``
alive.  In this simple case that's not really an issue, but imagine replacing
``SomeComputation`` with something more complicated that's holding onto
a system resource of some kind.  We want to find out what's keeping it alive,
and how we can fix the problem.  We run the above code under ``python -i``, and
take a snapshot::

    >>> import refcycle
    >>> snapshot = refcycle.snapshot()
    >>> snapshot
    <refcycle.object_graph.ObjectGraph object of size 5797 at 0x1004ca110>

An |ObjectGraph| acts as a container, so we can search through it for the
``SomeComputation`` instance::

    >>> computations = [obj for obj in snapshot
    ...                 if isinstance(obj, SomeComputation)]
    >>> computations
    [<__main__.SomeComputation object at 0x1004ca050>]
    >>> c = computations[0]

Now we can use the |ancestors| method to find out what's keeping references to
``c``.

    >>> snapshot.ancestors(c)
    <refcycle.object_graph.ObjectGraph object of size 5 at 0x10242db50>

In this particular case the graph of all ancestors is very small.  More
typically, that graph is much larger, so it's often convenient to limit the
search to a given number of generations, for example with::

    >>> snapshot.ancestors(c, generations=5)
    <refcycle.object_graph.ObjectGraph object of size 5 at 0x10242db10>

Either way, we can now export this graph as an image::

    >>> snapshot.ancestors(c).export_image('computations.svg')

This gives the following rather simple graph:

.. image:: images/computations.*

So it's the ``compute`` bound method keeping ``c`` alive (through its
``__self__`` reference).  What's keeping *that* alive is a *frame* object: the
execution frame for the long-running ``worker`` function.  Its local variable
``job`` is still referring to our bound method.  Looking back at the original
code, the cause is clear: the ``job`` local variable retains its reference to
the ``job`` until the ``get`` call on the job queue returns the *next* job.
But after the last job has been submitted, that ``get`` call waits forever, so
the reference to the last job never disappears.  And in this case the fix is
easy: add a ``del job`` to the end of the ``while`` loop::

    def worker(jobs_queue, results_queue):
        while True:
            job = jobs_queue.get()
            result = job()
            results_queue.put(result)
            del job

What about the other two frame objects in the graph?  The worker thread spends
almost all its time waiting, and that top frame is the current frame of the
worker thread.  It refers to the ``wait`` method of the
:py:class:`threading.Condition` object used by the jobs queue.  The ``f_back``
edge refers to the calling frame, in this case the :py:meth:`queue.Queue.get`
method call, whose ``f_back`` refers in turn to our ``worker`` function.


.. |ObjectGraph| replace:: :class:`~refcycle.object_graph.ObjectGraph`
.. |garbage| replace:: :func:`~refcycle.creators.garbage`
.. |snapshot| replace:: :func:`~refcycle.creators.snapshot`
.. |source_components| replace:: :meth:`~refcycle.i_directed_graph.IDirectedGraph.source_components`
.. |strongly_connected_components| replace:: :meth:`~refcycle.i_directed_graph.IDirectedGraph.strongly_connected_components`
.. |ancestors| replace:: :meth:`~refcycle.i_directed_graph.IDirectedGraph.ancestors`

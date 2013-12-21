Technical notes
---------------

Tracked objects
+++++++++++++++

The |snapshot| helper function returns a snapshot of all live Python objects
that are currently being tracked by the cyclic garbage collector; that's not
the same thing as all currently live Python objects.

In more detail: not all Python objects are tracked by the cyclic garbage collector.  Objects
like integers and strings have no references to other objects, so cannot be
involved in a cycle; so they're not tracked.  There's a
:py:func:`gc.is_tracked` function in the standard library that allows you to
find out whether an object is currently tracked or not::

    >>> import gc
    >>> a = 12.56
    >>> gc.is_tracked(a)
    False
    >>> gc.is_tracked(b)
    True

There are some surprises lurking, though:

    >>> a = 1, 2, 3
    >>> gc.is_tracked(a)
    True
    >>> gc.collect()
    0
    >>> gc.is_tracked(a)
    False

In current Python, there are some optimizations that untrack certain objects
when it's clear that they can't be involved in a cycle.  Those optimizations
run during garbage collection.  In the example above, the garbage collector
determined that none of the objects in the tuple ``a`` was tracked, so that
there's no need to track ``a`` either.

This means that you shouldn't depend on the set of tracked objects being too
predictable.  When diagnosing object leaks, it's tempting to compare lengths of
:py:func:`gc.get_objects` return values before and after some computation, but
since :py:func:`gc.get_objects` returns only the gc-tracked objects, those
lengths may change depending on the optimizations.  For example::

    >>> import gc
    >>> a = (((1, 2, 3), 4), (5, 6))
    >>> len(gc.get_objects())
    3586
    >>> gc.collect()
    0
    >>> len(gc.get_objects())
    3410
    >>> gc.collect()
    0
    >>> len(gc.get_objects())
    3409
    >>> gc.collect()
    0
    >>> len(gc.get_objects())
    3408
    >>> gc.collect()
    0
    >>> len(gc.get_objects())
    3408
    >>> gc.collect()
    0


Referrers versus referents
++++++++++++++++++++++++++

The |ObjectGraph| class fills in edges using :py:func:`gc.get_referents`,
rather than :py:func:`gc.get_referrers`.  There's an important difference
between the two functions: not only is :py:func:`gc.get_referrers` much slower
than :py:func:`gc.get_referents`; it would also return a smaller graph.  Python
objects that are trackable by the garbage collector provide a natural mechanism
for computing their referents (via the ``tp_traverse`` slot at C level), but
there's no simple way to find the referrers of a given object.  So
``gc.get_referrers(obj)`` traverses the entire list of current gc-tracked
objects looking for those which refer to ``obj``.  This is slower, and returns
only gc-tracked objects.


.. |ObjectGraph| replace:: :class:`~refcycle.object_graph.ObjectGraph`
.. |snapshot| replace:: :func:`~refcycle.creators.snapshot`

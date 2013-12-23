try:
    from queue import Queue  # Replace 'queue' with 'Queue' for Python 2.
except ImportError:
    from Queue import Queue
import threading


def worker(jobs_queue, results_queue):
    while True:
        job = jobs_queue.get()
        result = job()
        results_queue.put(result)


jobs_queue, results_queue = Queue(), Queue()
t = threading.Thread(target=worker, args=(jobs_queue, results_queue))
t.daemon = True
t.start()


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


import refcycle
snapshot = refcycle.snapshot()
c = next(c for c in snapshot if isinstance(c, SomeComputation))

snapshot.ancestors(c).export_image('computations.svg')

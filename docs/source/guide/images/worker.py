import threading
from queue import Queue

import refcycle


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


snapshot = refcycle.snapshot()
c = next(c for c in snapshot if isinstance(c, SomeComputation))

snapshot.ancestors(c).export_image("computations.svg")
snapshot.ancestors(c).export_image("computations.pdf")

frame = snapshot.parents(snapshot.parents(c)[0])[0]
print(repr(frame.f_code))
print(repr(frame.f_locals))

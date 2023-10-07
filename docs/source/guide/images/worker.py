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

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
from refcycle import cycles_created_by


class A(object):
    pass


def create_cycles():
    a, b, c = A(), A(), A()
    a.foo = b
    b.foo = a
    a.bar = c


graph = cycles_created_by(create_cycles)
print(graph.to_dot())

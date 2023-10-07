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
"""
Utilities for manipulating the garbage collector.

"""
import contextlib
import gc


@contextlib.contextmanager
def restore_gc_state():
    """
    Restore the garbage collector state on leaving the with block.

    """
    old_isenabled = gc.isenabled()
    old_flags = gc.get_debug()
    try:
        yield
    finally:
        gc.set_debug(old_flags)
        (gc.enable if old_isenabled else gc.disable)()

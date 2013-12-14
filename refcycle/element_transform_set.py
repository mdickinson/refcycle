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
A set-like object that transforms its elements for
internal storage, allowing non-hashable objects to be stored
efficiently.

"""
from collections import MutableSet

import six


class ElementTransformSet(MutableSet):
    """
    A set-like object that transforms its elements for
    internal storage, allowing non-hashable objects to be stored
    efficiently.

    """
    __slots__ = ('_transform', '_elements')

    def __init__(self, transform):
        self._transform = transform
        self._elements = {}

    def __contains__(self, element):
        return self._transform(element) in self._elements

    def __iter__(self):
        return six.itervalues(self._elements)

    def __len__(self):
        return len(self._elements)

    def add(self, element):
        """Add an element to this set."""
        key = self._transform(element)
        if key not in self._elements:
            self._elements[key] = element

    def discard(self, element):
        """Remove an element.  Do not raise an exception if absent."""
        key = self._transform(element)
        if key in self._elements:
            del self._elements[key]

    def update(self, iterable):
        for element in iterable:
            self.add(element)

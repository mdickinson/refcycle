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
A dict-like object that transforms its keys for internal storage,
allowing non-hashable keys to be used efficiently.

Similar to, and partly inspired by, Antoine Pitrou's TransformDict
implementation (bugs.python.org/issue18986).

"""
import collections

import six


class KeyTransformDict(collections.MutableMapping):
    """
    A dict-like object that transforms its keys for internal storage,
    allowing non-hashable keys to be used efficiently.

    """
    __slots__ = ('_transform', '_default_factory', '_keys', '_values')

    def __init__(self, transform, default_factory=None):
        self._transform = transform
        self._default_factory = default_factory
        self._keys = {}
        self._values = {}

    def __iter__(self):
        return six.itervalues(self._keys)

    def __len__(self):
        return len(self._keys)

    def __getitem__(self, key):
        transformed_key = self._transform(key)
        try:
            return self._values[transformed_key]
        except KeyError:
            if self._default_factory is None:
                raise KeyError(key)
            self._keys[transformed_key] = key
            return self._values.setdefault(
                transformed_key, self._default_factory())

    def __setitem__(self, key, value):
        transformed_key = self._transform(key)
        if transformed_key not in self._keys:
            self._keys[transformed_key] = key
        self._values[transformed_key] = value

    def __delitem__(self, key):
        transformed_key = self._transform(key)
        if transformed_key not in self._keys:
            raise KeyError(key)
        else:
            del self._keys[transformed_key]
            del self._values[transformed_key]

    def __contains__(self, key):
        transformed_key = self._transform(key)
        return transformed_key in self._keys

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
Tests for the ElementTransformSet class.

"""
import unittest

from refcycle.element_transform_set import ElementTransformSet


class TestElementTransformSet(unittest.TestCase):
    def test_add(self):
        s = ElementTransformSet(transform=lambda x: x*x)
        s.add(13)
        self.assertIn(13, s)

    def test_discard(self):
        s = ElementTransformSet(transform=lambda x: x*x)
        s.add(13)
        s.add(-14)
        # Discarding something in the set.
        s.discard(-13)
        self.assertIn(14, s)
        self.assertNotIn(13, s)
        # Discarding something not in the set.
        s.discard(17)

    def test_remove(self):
        s = ElementTransformSet(transform=lambda x: x*x)
        with self.assertRaises(KeyError) as cm:
            s.remove(3)
        # Make sure that the KeyError carries the original value,
        # not the transformed value.
        self.assertEqual(cm.exception.args, (3,))

    def test_len(self):
        s = ElementTransformSet(transform=lambda x: x*x + 1)
        self.assertEqual(len(s), 0)
        s.add(4)
        self.assertEqual(len(s), 1)
        s.add(5)
        self.assertEqual(len(s), 2)
        s.remove(-4)
        self.assertEqual(len(s), 1)
        s.remove(-5)
        self.assertEqual(len(s), 0)

    def test_iter(self):
        s = ElementTransformSet(transform=lambda x: x*x + 1)
        s.add(4)
        s.add(5)
        self.assertEqual(sorted(iter(s)), [4, 5])

    def test_update(self):
        s = ElementTransformSet(transform=lambda x: x*x + 1)
        s.update([5, 6, 7])
        self.assertEqual(sorted(s), [5, 6, 7])
        s.update([1, 2, 3])
        self.assertEqual(sorted(s), [1, 2, 3, 5, 6, 7])

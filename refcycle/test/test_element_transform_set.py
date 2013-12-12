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

from refcycle.test.element_transform_set import ElementTransformSet


class TestElementTransformSet(unittest.TestCase):
    def test_add_and_len(self):
        s = ElementTransformSet(transform=abs)
        self.assertEqual(len(s), 0)
        s.add(2)
        self.assertEqual(len(s), 1)

    def test_discard(self):
        s = ElementTransformSet(transform=abs)
        self.assertEqual(list(s), [])
        s.add(2)
        self.assertEqual(list(s), [2])
        s.discard(3)
        self.assertEqual(list(s), [2])
        s.discard(2)
        self.assertEqual(list(s), [])

    def test_bool(self):
        s = ElementTransformSet(transform=abs)
        self.assertFalse(s)
        s.add(23)
        self.assertTrue(s)

    def test_first_addition_takes_precedence(self):
        # Like a normal set.
        s = ElementTransformSet(transform=abs)
        s.add(23)
        s.add(-23)
        self.assertEqual(list(s), [23])
        s.add(23.0)
        self.assertEqual(list(s), [23])

    def test_from_iterable(self):
        s = ElementTransformSet(abs, [2, -6, 7])
        self.assertEqual(sorted(list(s)), [-6, 2, 7])

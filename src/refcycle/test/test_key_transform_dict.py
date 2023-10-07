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
Tests for the KeyTransformDict class.

"""
import unittest

from refcycle.key_transform_dict import KeyTransformDict


class TestKeyTransformDict(unittest.TestCase):
    def test_len(self):
        d = KeyTransformDict(transform=abs)
        self.assertEqual(len(d), 0)
        d[13] = 2
        self.assertEqual(len(d), 1)
        d[-14] = 5
        self.assertEqual(len(d), 2)
        d[-13] = 3
        self.assertEqual(len(d), 2)
        result = d.pop(13)
        self.assertEqual(result, 3)
        self.assertEqual(len(d), 1)
        del d[14]
        self.assertEqual(len(d), 0)

    def test_successful_lookup(self):
        d = KeyTransformDict(transform=lambda x: x.lower())
        d["Boris"] = "Becker"
        self.assertEqual(d["BORIS"], "Becker")

    def test_failed_lookup(self):
        d = KeyTransformDict(transform=abs)
        d[13] = 4
        with self.assertRaises(KeyError) as cm:
            d[-16]
        # Make sure that the KeyError carries the original key,
        # not the transformed key.
        self.assertEqual(cm.exception.args, (-16,))

    def test_del(self):
        d = KeyTransformDict(transform=lambda x: x*x)
        d[13] = 4
        del d[-13]
        with self.assertRaises(KeyError) as cm:
            del d[14]
        # Make sure that the KeyError carries the original key,
        # not the transformed key.
        self.assertEqual(cm.exception.args, (14,))

    def test_default_factory(self):
        d = KeyTransformDict(transform=abs, default_factory=list)
        d[2].append(4)
        d[-2].append(5)
        self.assertIn(-2, d)
        self.assertEqual(d[2], [4, 5])
        self.assertEqual(list(d.items()), [(2, [4, 5])])

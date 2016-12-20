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
import ctypes
import gc
import inspect
import sys
import unittest
import types
import weakref

import six

from refcycle.annotations import annotated_references, object_annotation


class NewStyle(object):
    def foo(self):
        return 42  # pragma: nocover


class OldStyle:
    pass


def f(x, y, z=3):
    """This is f's docstring."""
    pass  # pragma: nocover


def outer(x):
    def inner(y):
        return x + y  # pragma: nocover
    return inner


class TestEdgeAnnotations(unittest.TestCase):
    def check_description(self, obj, target, description):
        annotations = annotated_references(obj)
        self.assertIn(
            target,
            annotations,
            msg="{} not found in referents of {}".format(target, obj),
        )
        self.assertIn(description, annotations[target])

    def check_completeness(self, obj):
        # Check that all referents of obj are annotated.
        annotations = annotated_references(obj)
        referents = gc.get_referents(obj)
        for ref in referents:
            if not annotations[ref]:
                self.fail(
                    "Didn't find annotation from {} to {}".format(obj, ref)
                )
            annotations[ref].pop()

    def test_annotate_tuple(self):
        a = (1, 2, 3)
        self.check_description(a, a[0], "item[0]")
        self.check_completeness(a)

    def test_annotate_list(self):
        a = [3, 4, 5]
        self.check_description(a, a[2], "item[2]")
        self.check_completeness(a)

    def test_annotate_dict_values(self):
        d = {"foo": [1, 2, 3]}
        self.check_description(d, d["foo"], "value['foo']")
        self.check_completeness(d)

    def test_annotate_set(self):
        a, b, c = 1, 2, 3
        s = {a, b, c}
        self.check_description(s, a, "element")
        self.check_description(s, b, "element")
        self.check_completeness(s)

    def test_annotate_frozenset(self):
        a, b, c = 1, 2, 3
        s = frozenset([a, b, c])
        self.check_description(s, a, "element")
        self.check_description(s, b, "element")
        self.check_completeness(s)

    def test_annotate_function(self):
        self.check_description(f, f.__defaults__, "__defaults__")
        self.check_description(f, f.__globals__, "__globals__")
        self.check_completeness(f)

    def test_annotate_function_closure(self):
        f = outer(5)
        self.check_description(f, f.__defaults__, "__defaults__")
        self.check_description(f, f.__globals__, "__globals__")
        self.check_description(f, f.__closure__, "__closure__")
        self.check_completeness(f)

    def test_annotate_function_attributes(self):
        def f():
            pass
        f.extra_attribute = [1, 2, 3]
        self.check_description(f, f.__dict__, "__dict__")
        self.check_completeness(f)

    def test_annotate_cell(self):
        f = outer(5)
        cell = f.__closure__[0]
        self.check_description(cell, cell.cell_contents, "cell_contents")
        self.check_completeness(cell)

    def test_annotate_bound_method(self):
        obj = NewStyle()
        meth = obj.foo
        self.check_description(meth, NewStyle.__dict__['foo'], "__func__")
        self.check_description(meth, obj, "__self__")
        if six.PY2:
            self.check_description(meth, NewStyle, "im_class")
        self.check_completeness(meth)

    def test_annotate_unbound_method(self):
        meth = NewStyle.foo
        if six.PY2:
            self.check_description(meth, NewStyle.__dict__['foo'], "__func__")
            self.check_description(meth, NewStyle, "im_class")
        else:
            self.check_description(meth, meth.__qualname__, "__qualname__")
        self.check_completeness(meth)

    def test_annotate_weakref(self):
        a = set()

        def callback(ref):
            return 5

        ref = weakref.ref(a, callback)
        self.check_description(ref, callback, "__callback__")
        self.check_completeness(ref)

    def test_annotate_object(self):
        obj = NewStyle()
        self.check_completeness(obj)

    def test_annotate_new_style_class(self):
        cls = NewStyle
        self.check_description(cls, cls.__mro__, "__mro__")

    def test_annotate_frame(self):
        def some_function(x, y):
            z = 27
            pow(z, z)
            return inspect.currentframe()
        frame = some_function("a string", 97.8)
        self.check_completeness(frame)

    def test_annotate_frame_with_f_trace(self):
        def some_function(x, y):
            z = 27
            pow(z, z)
            return inspect.currentframe()

        def test_trace(frame, event, arg):
            return test_trace

        old_trace_function = sys.gettrace()
        sys.settrace(test_trace)
        try:
            frame = some_function("a string", 97.8)
        finally:
            sys.settrace(old_trace_function)
        self.check_completeness(frame)

    def test_annotate_getset_descriptor(self):
        class A(object):
            pass
        descr = A.__weakref__
        self.check_completeness(descr)

    if six.PY2:
        def test_annotate_old_style_object(self):
            obj = OldStyle()
            self.check_completeness(obj)

    if six.PY3:
        def test_annotate_function_annotations(self):
            namespace = {}
            exec("def annotated_function() -> int: pass", namespace)
            annotated_function = namespace['annotated_function']
            self.check_completeness(annotated_function)

        def test_annotate_function_kwdefaults(self):
            namespace = {}
            exec("def kwdefaults_function(*, a=3, b=4): pass", namespace)
            kwdefaults_function = namespace['kwdefaults_function']
            self.check_completeness(kwdefaults_function)


class TestObjectAnnotations(unittest.TestCase):
    def test_none(self):
        x = None
        self.assertEqual(
            object_annotation(x),
            "None",
        )

    def test_bool(self):
        x = True
        self.assertEqual(
            object_annotation(x),
            "True",
        )

    def test_int(self):
        x = 12345
        self.assertEqual(
            object_annotation(x),
            "12345",
        )

    def test_float(self):
        x = 12345.0
        self.assertEqual(
            object_annotation(x),
            "12345.0",
        )

    def test_complex(self):
        x = 2j
        self.assertEqual(
            object_annotation(x),
            repr(x),
        )

    def test_str(self):
        x = "hello world"
        self.assertEqual(
            object_annotation(x),
            repr(x),
        )

    def test_annotate_list(self):
        l = [1, 2]
        self.assertEqual(
            object_annotation(l),
            "list[2]",
        )

    def test_annotate_tuple(self):
        t = (1, 2, 3)
        self.assertEqual(
            object_annotation(t),
            "tuple[3]",
        )

    def test_annotate_dict(self):
        d = {1: 2, 3: 4, 5: 6}
        self.assertEqual(
            object_annotation(d),
            "dict[3]",
        )

    def test_annotate_function(self):
        self.assertEqual(
            object_annotation(f),
            "function\\nf",
        )

    def test_annotate_object(self):
        obj = NewStyle()
        self.assertEqual(
            object_annotation(obj),
            "object\\nrefcycle.test.test_annotations.NewStyle",
        )

    if six.PY2:
        def test_annotate_old_style_object(self):
            obj = OldStyle()
            self.assertEqual(
                object_annotation(obj),
                "instance\\nOldStyle",
            )

    def test_annotate_new_style_class(self):
        self.assertEqual(
            object_annotation(NewStyle),
            "type\\nNewStyle",
        )

    def test_annotate_bound_method(self):
        method = NewStyle().foo
        self.assertEqual(
            object_annotation(method),
            "instancemethod\\nNewStyle.foo",
        )

    if six.PY2:
        def test_annotate_instancemethod_without_class(self):
            # In Python 2, it's possible to create bound methods
            # without an im_class attribute.
            def my_method(self):
                return 42

            method = types.MethodType(my_method, NewStyle())
            self.assertEqual(
                object_annotation(method),
                "instancemethod\\n<None>.my_method",
            )

    def test_annotate_instancemethod_with_nameless_function(self):
        # Regression test for mdickinson/refcycle#25.

        # Create a nameless function: comparison_function.__name__
        # raise AttributeError.
        comparison_function_type = ctypes.CFUNCTYPE(
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int),
        )
        comparison_function = comparison_function_type(lambda a, b: 0)

        method = types.MethodType(comparison_function, NewStyle())
        if six.PY2:
            expected = "instancemethod\\n<None>.<anonymous>"
        else:
            expected = "instancemethod\\n<anonymous>"

        self.assertEqual(object_annotation(method), expected)

    def test_annotate_weakref(self):
        a = set()
        ref = weakref.ref(a)
        self.assertEqual(
            object_annotation(ref),
            "weakref to id 0x{:x}".format(id(a)),
        )

    def test_annotate_weakref_to_dead_referent(self):
        a = set()
        ref = weakref.ref(a)
        del a
        self.assertEqual(
            object_annotation(ref),
            "weakref (dead referent)",
        )

    def test_annotate_frame(self):
        def some_function(x, y):
            z = 27
            pow(z, z)
            return inspect.currentframe()
        frame = some_function("a string", 97.8)
        annotation = object_annotation(frame)
        self.assertTrue(annotation.startswith("frame\\n"))
        self.assertIn("test_annotations", annotation)

    def test_annotate_module(self):
        annotation = object_annotation(weakref)
        self.assertTrue(annotation.startswith("module\\n"))
        self.assertIn("weakref", annotation)

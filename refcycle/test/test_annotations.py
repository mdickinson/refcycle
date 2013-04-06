import unittest

from refcycle.annotations import annotated_references


class TestAnnotations(unittest.TestCase):
    def check_description(self, annotations, obj, description):
        obj_id = id(obj)
        self.assertIn(obj_id, annotations)
        self.assertIn(description, annotations[obj_id])

    def test_annotate_tuple(self):
        a = (1, 2, 3)
        annotations = annotated_references(a)
        self.check_description(annotations, a[0], "item at index 0")

    def test_annotate_list(self):
        a = [3, 4, 5]
        annotations = annotated_references(a)
        self.check_description(annotations, a[2], "item at index 2")

    def test_annotate_dict_values(self):
        d = {"foo": [1, 2, 3]}
        annotations = annotated_references(d)
        self.check_description(annotations, d["foo"], "value for key foo")

    def test_annotate_function(self):
        def f(x, y, z=3):
            pass
        f(1, 2, 6)
        annotations = annotated_references(f)
        self.check_description(annotations, f.func_defaults, "func_defaults")
        self.check_description(annotations, f.func_globals, "func_globals")

    def test_annotate_function_closure(self):
        def outer(x):
            def inner(y):
                return x + y
            return inner
        f = outer(5)
        f(3)
        annotations = annotated_references(f)
        self.check_description(annotations, f.func_defaults, "func_defaults")
        self.check_description(annotations, f.func_globals, "func_globals")
        self.check_description(annotations, f.func_closure, "func_closure")

    def test_annotate_cell(self):
        def outer(x):
            def inner(y):
                return x + y
            return inner
        f = outer(5)
        f(3)
        cell = f.func_closure[0]
        annotations = annotated_references(cell)
        self.check_description(annotations,
                               cell.cell_contents, "cell_contents")

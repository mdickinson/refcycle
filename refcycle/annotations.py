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
Code to annotate edges and objects.

"""
import collections
import gc
import types
import weakref


def _get_cell_type():
    def f(x=None):
        return lambda: x
    return type(f().func_closure[0])

CellType = _get_cell_type()


def add_attr(obj, attr, references):
    if hasattr(obj, attr):
        references[id(getattr(obj, attr))].append(attr)


def add_cell_references(obj, references):
    add_attr(obj, "cell_contents", references)


def add_function_references(obj, references):
    # Not annotating func_code, __name__ and __module__ references.
    add_attr(obj, "func_defaults", references)
    add_attr(obj, "func_closure", references)
    add_attr(obj, "func_globals", references)
    add_attr(obj, "func_code", references)
    add_attr(obj, "__name__", references)
    add_attr(obj, "__module__", references)
    add_attr(obj, "__doc__", references)


def add_sequence_references(obj, references):
    for position, item in enumerate(obj):
        references[id(item)].append("item[{}]".format(position))


def add_dict_references(obj, references):
    for key, value in obj.iteritems():
        references[id(key)].append("key")
        references[id(value)].append("value[{0!r}]".format(key))


def add_set_references(obj, references):
    for elt in obj:
        references[id(elt)].append("element")


def add_bound_method_references(obj, references):
    add_attr(obj, "im_self", references)
    add_attr(obj, "im_func", references)
    add_attr(obj, "im_class", references)


def add_weakref_references(obj, references):
    # For subclasses of weakref, we can't reliably distinguish the
    # callback (if any) from other attributes.
    if type(obj) is weakref.ref:
        referents = gc.get_referents(obj)
        if len(referents) == 1:
            target = referents[0]
            references[id(target)].append("__callback__")


type_based_references = {
    tuple: add_sequence_references,
    list: add_sequence_references,
    dict: add_dict_references,
    set: add_set_references,
    frozenset: add_set_references,
    types.FunctionType: add_function_references,
    CellType: add_cell_references,
    types.MethodType: add_bound_method_references,
    weakref.ref: add_weakref_references,
}


def annotated_references(obj):
    """
    Return known information about references held by the given object.

    Returns a dictionary mapping ids of referents to lists of descriptions.
    Descriptions are currently strings.

    """
    references = collections.defaultdict(list)
    for type_ in type(obj).__mro__:
        if type_ in type_based_references:
            type_based_references[type_](obj, references)

    add_attr(obj, "__dict__", references)
    add_attr(obj, "__class__", references)
    if isinstance(obj, type):
        add_attr(obj, "__mro__", references)

    return references

###############################################################################
# Object annotations.


def object_annotation(obj):
    """
    Return a string to be used for GraphViz nodes.  The string
    should be short but as informative as possible.

    """
    if type(obj).__name__ == 'function':
        return "function\\n{}".format(obj.__name__)
    elif isinstance(obj, types.MethodType):
        return "instancemethod\\n{}.{}".format(
            obj.im_class.__name__,
            obj.im_func.__name__,
        )
    elif isinstance(obj, list):
        return "list[{}]".format(len(obj))
    elif isinstance(obj, tuple):
        return "tuple[{}]".format(len(obj))
    elif isinstance(obj, dict):
        return "dict[{}]".format(len(obj))
    elif isinstance(obj, type):
        return "type\\n{}".format(obj.__name__)
    elif isinstance(obj, types.InstanceType):
        return "instance\\n{}".format(obj.__class__.__name__)
    elif isinstance(obj, weakref.ref):
        referent = obj()
        if referent is None:
            return "weakref (dead referent)"
        else:
            return "weakref to id 0x{:x}".format(id(referent))
    else:
        return "object\\n{}.{}".format(
            type(obj).__module__,
            type(obj).__name__,
        )

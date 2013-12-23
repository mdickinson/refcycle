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
import gc
import types
import weakref

import six

from refcycle.key_transform_dict import KeyTransformDict

# Maximum number of characters to print in a frame filename.
FRAME_FILENAME_LIMIT = 30


def _get_cell_type():
    def f(x=None):
        return lambda: x
    return type(f().__closure__[0])


CellType = _get_cell_type()


def add_attr(obj, attr, references):
    if hasattr(obj, attr):
        references[getattr(obj, attr)].append(attr)


def add_cell_references(obj, references):
    add_attr(obj, "cell_contents", references)


def add_function_references(obj, references):
    add_attr(obj, "__defaults__", references)
    add_attr(obj, "__closure__", references)
    add_attr(obj, "__globals__", references)
    add_attr(obj, "__code__", references)
    add_attr(obj, "__name__", references)
    add_attr(obj, "__module__", references)
    add_attr(obj, "__doc__", references)
    if six.PY3:
        # Assumes version >= 3.3.
        add_attr(obj, "__qualname__", references)
        add_attr(obj, "__annotations__", references)
        add_attr(obj, "__kwdefaults__", references)


def add_sequence_references(obj, references):
    for position, item in enumerate(obj):
        references[item].append("item[{}]".format(position))


def add_dict_references(obj, references):
    for key, value in six.iteritems(obj):
        references[key].append("key")
        references[value].append("value[{0!r}]".format(key))


def add_set_references(obj, references):
    for elt in obj:
        references[elt].append("element")


def add_bound_method_references(obj, references):
    add_attr(obj, "__self__", references)
    add_attr(obj, "__func__", references)
    add_attr(obj, "im_class", references)


def add_weakref_references(obj, references):
    # For subclasses of weakref, we can't reliably distinguish the
    # callback (if any) from other attributes.
    if type(obj) is weakref.ref:
        referents = gc.get_referents(obj)
        if len(referents) == 1:
            target = referents[0]
            references[target].append("__callback__")


def add_frame_references(obj, references):
    add_attr(obj, "f_back", references)
    add_attr(obj, "f_code", references)
    add_attr(obj, "f_builtins", references)
    add_attr(obj, "f_globals", references)
    # The f_locals dictionary is only created on demand,
    # and then cached.
    add_attr(obj, "f_locals", references)
    for name, local in six.iteritems(obj.f_locals):
        references[local].append("local {!r}".format(name))


type_based_references = {
    tuple: add_sequence_references,
    list: add_sequence_references,
    dict: add_dict_references,
    set: add_set_references,
    frozenset: add_set_references,
    types.FunctionType: add_function_references,
    types.FrameType: add_frame_references,
    CellType: add_cell_references,
    types.MethodType: add_bound_method_references,
    weakref.ref: add_weakref_references,
}


def annotated_references(obj):
    """
    Return known information about references held by the given object.

    Returns a mapping from referents to lists of descriptions.  Note that there
    may be more than one edge leading to any particular referent; hence the
    need for a list.  Descriptions are currently strings.

    """
    references = KeyTransformDict(transform=id, default_factory=list)
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


BASE_TYPES = (
    six.integer_types +
    (float, complex, type(None), six.text_type, six.binary_type)
)


def object_annotation(obj):
    """
    Return a string to be used for Graphviz nodes.  The string
    should be short but as informative as possible.

    """
    # For basic types, use the repr.
    if isinstance(obj, BASE_TYPES):
        return repr(obj)
    if type(obj).__name__ == 'function':
        return "function\\n{}".format(obj.__name__)
    elif isinstance(obj, types.MethodType):
        if six.PY2:
            return "instancemethod\\n{}.{}".format(
                obj.im_class.__name__,
                obj.__func__.__name__,
            )
        else:
            return "instancemethod\\n{}".format(
                obj.__func__.__qualname__
            )
    elif isinstance(obj, list):
        return "list[{}]".format(len(obj))
    elif isinstance(obj, tuple):
        return "tuple[{}]".format(len(obj))
    elif isinstance(obj, dict):
        return "dict[{}]".format(len(obj))
    elif isinstance(obj, type):
        return "type\\n{}".format(obj.__name__)
    elif six.PY2 and isinstance(obj, types.InstanceType):
        return "instance\\n{}".format(obj.__class__.__name__)
    elif isinstance(obj, weakref.ref):
        referent = obj()
        if referent is None:
            return "weakref (dead referent)"
        else:
            return "weakref to id 0x{:x}".format(id(referent))
    elif isinstance(obj, types.FrameType):
        filename = obj.f_code.co_filename
        if len(filename) > FRAME_FILENAME_LIMIT:
            filename = "..." + filename[-(FRAME_FILENAME_LIMIT-3):]
        return "frame\\n{}:{}".format(
            filename,
            obj.f_code.co_firstlineno,
        )
    else:
        return "object\\n{}.{}".format(
            type(obj).__module__,
            type(obj).__name__,
        )

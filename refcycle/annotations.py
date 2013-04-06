"""
Code to annotate edges and objects.

"""
import collections
import types


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


def add_sequence_references(obj, references):
    for position, item in enumerate(obj):
        references[id(item)].append("item at index {}".format(position))


def add_dict_references(obj, references):
    for key, value in obj.iteritems():
        references[id(value)].append("value for key {}".format(key))


type_based_references = {
    tuple: add_sequence_references,
    list: add_sequence_references,
    dict: add_dict_references,
    types.FunctionType: add_function_references,
    CellType: add_cell_references,
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


def object_annotation(obj):
    """
    Return a string to be used for GraphViz nodes.  The string
    should be short but as informative as possible.

    """
    if type(obj).__name__ == 'function':
        return "function\\n{}".format(obj.__name__)
    elif isinstance(obj, tuple):
        return "tuple of length {}".format(len(obj))
    elif isinstance(obj, dict):
        return "dict of size {}".format(len(obj))
    elif isinstance(obj, type):
        return "type\\n{}".format(obj.__name__)
    elif isinstance(obj, types.InstanceType):
        return "instance\\n{}".format(obj.__class__.__name__)
    else:
        return type(obj).__name__

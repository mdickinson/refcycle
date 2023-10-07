# Configuration file for the Sphinx documentation builder.

import importlib.metadata

project = "refcycle"
copyright = "2013-2023 Mark Dickinson"
author = "Mark Dickinson"
release = importlib.metadata.version("refcycle")

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
]
add_function_parentheses = False
nitpicky = True

# -- Options for HTML output -------------------------------------------------
html_theme = "alabaster"

# -- Intersphinx configuration -----------------------------------------------
intersphinx_mapping = {"python": ("http://docs.python.org/3/", None)}

# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

# sys.path.insert(0, os.path.abspath('../docs'))
sys.path.insert(0, os.path.abspath('..'))
# sys.path.insert(0, os.path.abspath('.'))
print("Python search paths:")
for path in sys.path:
    print(path)

html_context = {'github_user_name': 'OliverDrechsler', 'github_repo_name': 'front_door_intercom_automation','project_name': 'Front Door intercom automation'}



# -- Project information -----------------------------------------------------

project = 'Front door intercom automation'
copyright = '2020, Oliver Drechsler'
author = 'Oliver Drechsler'

# The full version, including alpha/beta/rc tags
release = '1.0.0'

# -- General configuration ---------------------------------------------------

# Paths for the documents
source_suffix = ['.rst', '.md']

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    # 'myst_parser',  # For Markdown support
    'sphinx.ext.napoleon',  # For Google style docstrings
    'sphinx.ext.viewcode',  # Add links to highlighted source code
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'recommonmark',
    'sphinx_md',
    'sphinx.ext.githubpages',
    'sphinx.ext.todo',
]

# If you use MyST-Parser for Markdown
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "html_admonition",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "strikethrough",
    "substitution",
    "tasklist",
]

# Adding custom sidebar templates, must be a dictionary that maps document names
# to template names.
html_sidebars = {
    '**': [
        'globaltoc.html',
        'relations.html',  # needs 'show_related': True theme option to display
        'searchbox.html',
    ]
}


# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['fdia2', 'fdia3', 'get_otp_token', 'otp_token_helper_cli']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
#html_theme = 'alabaster'
html_theme = 'sphinx_rtd_theme'
# html_theme = 'classic'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']


# -- Extension configuration -------------------------------------------------


from os import getenv

sphinx_md_useGitHubURL = True
baseBranch = "master"
commitSHA = getenv('GITHUB_SHA')
githubBaseURL = 'https://github.com/' + (getenv('GITHUB_REPOSITORY') or 'OliverDrechsler/front_door_intercom_automation') + '/'
githubFileURL = githubBaseURL + "blob/"
githubDirURL = githubBaseURL + "tree/"
if commitSHA:
    githubFileURL = githubFileURL + commitSHA + "/"
    githubDirURL = githubDirURL + commitSHA + "/"
else:
    githubFileURL = githubFileURL + baseBranch + "/"
    githubDirURL = githubDirURL + baseBranch + "/"
sphinx_md_githubFileURL = githubFileURL
sphinx_md_githubDirURL = githubDirURL
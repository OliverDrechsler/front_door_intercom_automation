import os
import sys
from os import getenv

from recommonmark.parser import CommonMarkParser

## sys.path.insert(0, os.path.abspath('../'))
# Add project root so autodoc can import the package/module
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# -- Project information -----------------------------------------------------

project = 'Front door intercom automation'
copyright = '2020, Oliver Drechsler'
author = 'Oliver Drechsler'

# The full version, including alpha/beta/rc tags
release = '1.0.0'

# -- General configuration ---------------------------------------------------

extensions = ['sphinx.ext.autodoc',
              'sphinx.ext.githubpages',  # Keep this one
              'myst_parser',
              'sphinx_md',
              'sphinx.ext.todo', ]

templates_path = ['_templates']

# -- Options for HTML output -------------------------------------------------

# HTML output
html_theme = "sphinx_rtd_theme"

html_context = {'github_user_name': 'OliverDrechsler', 'github_repo_name': 'front_door_intercom_automation',
                'project_name': 'Front Door intercom automation'}
html_static_path = ['_static']

# -- Extension configuration -------------------------------------------------


source_parsers = {'.md': CommonMarkParser, }

source_suffix = ['.rst', '.md']

sphinx_md_useGitHubURL = True
baseBranch = "master"
commitSHA = getenv('GITHUB_SHA')
githubBaseURL = 'https://github.com/' + (
        getenv('GITHUB_REPOSITORY') or 'OliverDrechsler/front_door_intercom_automation') + '/'
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

# Autodoc options
autodoc_member_order = "bysource"
autodoc_typehints = "description"

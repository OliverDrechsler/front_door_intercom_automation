import os
import sys

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
              'sphinx.ext.todo', ]

templates_path = ['_templates']

# -- Options for HTML output -------------------------------------------------

# HTML output
html_theme = "sphinx_rtd_theme"

html_context = {'github_user_name': 'OliverDrechsler', 'github_repo_name': 'front_door_intercom_automation',
                'project_name': 'Front Door intercom automation'}
html_static_path = []

# -- Extension configuration -------------------------------------------------


source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# Keep the docs build independent from the application's runtime dependencies.
autodoc_mock_imports = [
    'aiohttp',
    'astral',
    'blinkpy',
    'flask',
    'flask_httpauth',
    'PIL',
    'pyotp',
    'requests',
    'telebot',
    'werkzeug',
    'yaml',
]

# Autodoc options
autodoc_member_order = "bysource"
autodoc_typehints = "description"

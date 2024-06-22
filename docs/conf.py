#  Copyright (C) 2020 Michel Gokan Khan
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along
#  with this program; if not, write to the Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
#  This file is a part of the PerfSim project, which is now open source and available under the GPLv2.
#  Written by Michel Gokan Khan, February 2020


import os
import sys

sys.path.insert(0, os.path.abspath('..'))
sys.setrecursionlimit(1500)

# -- Project information -----------------------------------------------------

project = 'PerfSim'
copyright = '2022, Michel Gokan Khan'
author = 'Michel Gokan Khan'

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.viewcode',
    'sphinx.ext.todo',
    'rst2pdf.pdfbuilder',
    "pallets_sphinx_themes",
    # "sphinxcontrib.log_cabinet",
    "sphinx_issues",
    "sphinx_autodoc_typehints",
    # 'myst_parser',
    'm2r2',
]
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource'
    # 'special-members': '__init__.py'
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = 'en'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', 'tests/*', '../tests/*', 'tests']

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
# html_theme = 'jinja'
# html_theme = 'sizzle'
# html_theme = 'alabaster'
html_theme = 'sphinx_book_theme'
html_theme_options = {
    # "rightsidebar": "true",
    # "relbarbgcolor": "black",
    "repository_url": "https://github.com/michelgokan/perfsim",
    "use_repository_button": True,
    "use_issues_button": True,
    "use_download_button": True,
}

html_logo = "_static/logo/perfsim-logo.png"
html_favicon = "_static/logo/perfsim-logo.png"
html_title = "PerfSim: A Performance Simulator for Cloud-naive Computing"
# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
html_css_files = [
    'css/custom.css',
]
html_js_files = [
    'js/custom.js'
]
pygments_style = 'sphinx'
add_module_names = True
autoclass_content = 'init'
set_type_checking_flag = False
always_document_param_types = True
autodoc_typehints = 'description'
# -- Extension configuration -------------------------------------------------

# -- Options for todo extension ----------------------------------------------

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True
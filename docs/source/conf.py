# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

sys.path.insert(0, os.path.abspath('../..'))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'qteasy'
copyright = '2023, Jackie PENG'
author = 'Jackie PENG'
version = '1.4'
release = '1.4.9'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

source_parsers = {
    '.md': 'recommonmark.parser.CommonMarkParser',
}

source_suffix = ['.rst', '.md']

extensions = [
    'myst_parser',  # myst_parser should be installed with 'pip install myst-parser'
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.autosummary',
    'sphinx.ext.viewcode',
    # 'sphinx-markdown-checkbox',
]

templates_path = ['_templates']
exclude_patterns = []

language = 'en'  # set the language for the documentation, 'en' for English
locale_dirs = ['locale/']  # directory where translation templates are stored
gettext_compact = False

# configurations of myst_parser for math equations and others

myst_heading_anchors = 3  # generate anchors for headings up to level 3 for myst markdown files

myst_enable_extensions = [
    "amsmath",  # enables direct LaTeX math equations like: \begin{equation} ... \end{equation}
    "attrs_inline",  # parse inline attributes like {attr} in markdown
    "colon_fence",  # enables ::: for code blocks, useful for admonitions that uses ::: syntax
    "deflist",  # create definition lists like:
    # term
    # : definition
    "dollarmath",  # enables $...$ for inline math and $$...$$ for display math equations
    "fieldlist",  # allows field lists in markdown, useful for metadata like:
    # :field1: value1
    # :field2: value2
    "html_image",  # allows HTML image tags in markdown
    "replacements",  # automatically converts some special characters like (C), (TM), etc.
    "tasklist",  # enables task lists with checkboxes in markdown, like:
    # - [ ] Task 1
    # - [x] Task 2 (completed)
]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'  # other popular themes include 'alabaster', 'classic', 'sphinx_rtd_theme'
html_static_path = ['_static']
html_logo = "NESDRA_Logo.png"
html_theme_options = {
    'logo_only': True,
    'display_version': False,
}

# -- Latex options ---------------------------------------------------------
# latex options are used for format of PDF documentation from the source files
latex_engine = 'xelatex'
latex_elements = {
    'papersize': 'a4paper',  # set paper size
    'extraclassoptions': 'openany,oneside',  # prevent page breaks between chapters
    # set the style of preamble and toc
    'preamble': r''' 
\usepackage[titles]{tocloft}
\cftsetpnumwidth {1.25cm}\cftsetrmarg{1.5cm}
\setlength{\cftchapnumwidth}{0.75cm}
\setlength{\cftsecindent}{\cftchapnumwidth}
\setlength{\cftsecnumwidth}{1.25cm}
''',
    'sphinxsetup': 'TitleColor=DarkGoldenrod',  # set the color of the title in the preamble
    'fncychap': r'\usepackage[Bjornstrup]{fncychap}',   # "Sonny", “Lenny”, “Glenn”, “Conny”, “Rejne” and “Bjornstrup”
}

# Configuration file for the Sphinx documentation builder.
# duvc-ctl - USB Video Class Camera Control Library

import os
import sys
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

# Add project root and Python bindings to path for autodoc
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "bindings" / "python"))
sys.path.insert(0, str(project_root))

# Allow Sphinx to discover .md files outside sphinx/ directory
source_parent = Path(__file__).parent.parent
sys.path.insert(0, str(source_parent))


# -- Project information -----
project = 'duvc-ctl'
copyright = '2025, allanhanan'
author = 'allanhanan'
version = '2.0.0'
release = '2.0.0'

# -- General configuration ---
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.extlinks',
    'sphinx.ext.todo',
    'sphinx.ext.autosectionlabel',
    'breathe',
    'myst_parser',
    'sphinx_design',
    'sphinx_copybutton',
]

autosectionlabel_prefix_document = True

# -- Breathe Configuration (Doxygen Integration) ---
breathe_projects = {
    "duvc-ctl": "../build/doxygen/xml"
}
breathe_default_project = "duvc-ctl"
breathe_domain_by_extension = {
    "h": "cpp",
    "hpp": "cpp",
    "cpp": "cpp",
}

# -- Source file suffixes ---
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# -- MyST Parser Configuration ---
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "fieldlist",
    "html_admonition",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "substitution",
    "tasklist",
]

myst_heading_anchors = 3
suppress_warnings = [
    'myst.header_anchor',
    'ref.citation',
    'app.add_locale',
    'autosectionlabel.nolabel',
    'myst.xref_missing',
]

autosectionlabel_prefix_document = True

# Disable strict warning mode for included content
warningiserror = False

# Handle markdown internal links better
myst_heading_anchors = 3
myst_substitutions = {}

highlight_options = {'stripnl': False}
pygments_style = 'default'


# -- HTML output (RTD Theme) ---
html_theme = 'shibuya'

html_theme_options = {
    "github_url": "https://github.com/allanhanan/duvc-ctl",
}

html_static_path = []
html_css_files = []
html_js_files = []

html_title = f"{project} v{version} Documentation"
html_short_title = f"{project} v{version}"
html_use_index = True
html_split_index = False
html_show_sourcelink = True
html_show_sphinx = False
html_show_copyright = True
html_last_updated_fmt = '%b %d, %Y'
html_domain_indices = True
html_use_modindex = True

# -- AutoDoc Configuration ---
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__,__dict__,__module__',
    'show-inheritance': True,
}
autodoc_typehints = 'description'
autodoc_typehints_description_target = 'documented'
autodoc_class_signature = 'mixed'
autodoc_member_order = 'bysource'

# -- Napoleon Configuration ---
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# -- Intersphinx Configuration ---
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'cmake': ('https://cmake.org/cmake/help/latest/', None),
}
intersphinx_disabled_reftypes = ["*"]

# -- External links ---
extlinks = {
    'issue': ('https://github.com/allanhanan/duvc-ctl/issues/%s', 'issue #%s'),
    'pr': ('https://github.com/allanhanan/duvc-ctl/pull/%s', 'PR #%s'),
    'commit': ('https://github.com/allanhanan/duvc-ctl/commit/%s', 'commit %s'),
    'pypi': ('https://pypi.org/project/%s/', '%s'),
}

# -- Copy Button Configuration ---
copybutton_prompt_text = r">>> |\.\.\.|\$ |In \[\d*\]:|"
copybutton_prompt_is_regexp = True
copybutton_only_copy_prompt_lines = True
copybutton_remove_prompts = True
copybutton_copy_empty_lines = False
copybutton_line_continuation_character = "\\"

# -- Todo Configuration ---
todo_include_todos = True
todo_emit_warnings = False

# -- Manual page output ---
man_pages = [
    ('cli/index', 'duvc-cli', 'duvc-ctl Command Line Interface', [author], 1)
]

# -- Texinfo output ---
texinfo_documents = [
    ('index', 'duvc-ctl', 'duvc-ctl Documentation',
     author, 'duvc-ctl', 'USB Video Class Camera Control Library',
     'Miscellaneous'),
]

# -- Epub output ---
epub_title = project
epub_author = author
epub_publisher = author
epub_copyright = copyright
epub_exclude_files = ['search.html']

# -- Suppress warnings ---
suppress_warnings = [
    'myst.header',
    'ref.citation',
    'app.add_locale',
]

def setup(app):
    """Register Sphinx event handlers."""
    # Disable Shibuya's broken ToC XML parser by replacing its handler
    # We'll set toc to empty to skip the broken code path
    def skip_shibuya_toc_patch(app, pagename, templatename, context, doctree):
        # Shibuya will get an empty toc and skip its broken _fix_context_toc()
        context["toc"] = ""
    
    app.connect("html-page-context", skip_shibuya_toc_patch, priority=-100)
# Configuration file for the Sphinx documentation builder.

# duvc-ctl - USB Video Class Camera Control Library

import os
import sys
from pathlib import Path

# Add project root and Python bindings to path for autodoc
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "bindings" / "python"))
sys.path.insert(0, str(project_root))

# -- Project information -----------------------------------------------------

project = 'duvc-ctl'
copyright = '2025, allanhanan'
author = 'allanhanan'

# Version information
version = '2.0.0'
release = '2.0.0'

# -- General configuration ---------------------------------------------------

extensions = [
    # Core Sphinx extensions
    'sphinx.ext.autodoc',  # Automatic documentation from docstrings
    'sphinx.ext.autosummary',  # Generate summary tables
    'sphinx.ext.viewcode',  # Add source code links
    'sphinx.ext.napoleon',  # Support for NumPy and Google style docstrings
    'sphinx.ext.intersphinx',  # Link to other projects' documentation
    'sphinx.ext.extlinks',  # Shortened external links
    'sphinx.ext.todo',  # Todo items
    'sphinx.ext.coverage',  # Documentation coverage checker
    'sphinx.ext.autosectionlabel',  # Auto-generate section labels for refs

    # Doxygen integration
    'breathe',  # Bridge between Sphinx and Doxygen

    # Modern documentation features
    'myst_parser',  # Markdown support
    'sphinx_design',  # Modern UI components (cards, grids, etc.)
    'sphinx_copybutton',  # Copy code button
    'sphinx_togglebutton',  # Collapsible sections
    'sphinxext.opengraph',  # Open Graph meta tags for social media
    'notfound.extension',  # Custom 404 page
    'sphinx_sitemap',  # Generate sitemap.xml
]

autosectionlabel_prefix_document = True  # Fix duplicate labels

# -- Breathe Configuration (Doxygen Integration) ----------------------------

breathe_projects = {
    "duvc-ctl": "../build/doxygen/xml"  # Adjusted path; verify this points to actual XML location
}

breathe_default_project = "duvc-ctl"
breathe_domain_by_extension = {
    "h": "cpp",
    "hpp": "cpp",
    "cpp": "cpp",
}

# -- Source file suffixes ---------------------------------------------------

source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# -- MyST Parser Configuration ----------------------------------------------

myst_enable_extensions = [
    "colon_fence",  # ::: fences
    "deflist",  # Definition lists
    "fieldlist",  # Field lists
    "html_admonition",  # HTML-style admonitions
    "html_image",  # HTML-style images
    "linkify",  # Auto-link URLs
    "replacements",  # Text replacements
    "smartquotes",  # Smart quotes
    "substitution",  # Variable substitutions
    "tasklist",  # GitHub-style task lists
]

# -- HTML output options ----------------------------------------------------

html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    # Analytics
    'analytics_id': '',
    'analytics_anonymize_ip': False,

    # Display options
    'logo_only': False,
    'prev_next_buttons_location': 'both',
    'style_external_links': True,
    'vcs_pageview_mode': 'blob',

    # Navigation
    'collapse_navigation': False,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False,

    # Theme colors
    'style_nav_header_background': '#2980B9',
}

# Static files (CSS, JavaScript, images)
html_static_path = ['_static']
html_css_files = [
    'custom.css',
    'colors.css',
]
html_js_files = [
    'custom.js',
]

# HTML output options
html_title = f"{project} v{version} Documentation"
html_short_title = f"{project} v{version}"
# html_logo = '_static/duvc-logo.png'  # Removed to avoid warning; add back with real file
# html_favicon = '_static/favicon.ico'  # Removed to avoid warning; add back with real file
html_use_index = True
html_split_index = False
html_show_sourcelink = True
html_show_sphinx = False
html_show_copyright = True
html_last_updated_fmt = '%b %d, %Y'
html_domain_indices = True
html_use_modindex = True

# -- AutoDoc Configuration --------------------------------------------------

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

# -- Napoleon Configuration (Google/NumPy docstring style) ------------------

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

# -- Intersphinx Configuration ----------------------------------------------

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'cmake': ('https://cmake.org/cmake/help/latest/', None),
}

intersphinx_disabled_reftypes = ["*"]

# -- External links ---------------------------------------------------------

extlinks = {
    'issue': ('https://github.com/allanhanan/duvc-ctl/issues/%s', 'issue #%s'),
    'pr': ('https://github.com/allanhanan/duvc-ctl/pull/%s', 'PR #%s'),
    'commit': ('https://github.com/allanhanan/duvc-ctl/commit/%s', 'commit %s'),
    'pypi': ('https://pypi.org/project/%s/', '%s'),
}

# -- Copy Button Configuration ----------------------------------------------

copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True
copybutton_only_copy_prompt_lines = True
copybutton_remove_prompts = True
copybutton_copy_empty_lines = False
copybutton_line_continuation_character = "\\"

# -- Open Graph Configuration -----------------------------------------------

ogp_site_url = 'https://allanhanan.github.io/duvc-ctl/'
ogp_description_length = 200
ogp_image = '_static/images/social-card.png'
ogp_social_cards = {
    "enable": True,
}

# -- Sitemap Configuration --------------------------------------------------

html_baseurl = 'https://allanhanan.github.io/duvc-ctl/'
sitemap_url_scheme = "{link}"

# -- Todo Configuration -----------------------------------------------------

todo_include_todos = True
todo_emit_warnings = False

# -- Options for manual page output ------------------------------------------

man_pages = [
    ('cli/index', 'duvc-cli', 'duvc-ctl Command Line Interface', [author], 1)
]

# -- Options for Texinfo output ---------------------------------------------

texinfo_documents = [
    ('index', 'duvc-ctl', 'duvc-ctl Documentation',
     author, 'duvc-ctl', 'USB Video Class Camera Control Library',
     'Miscellaneous'),
]

# -- Options for Epub output ------------------------------------------------

epub_title = project
epub_author = author
epub_publisher = author
epub_copyright = copyright
epub_exclude_files = ['search.html']

# -- Custom processing ------------------------------------------------------

def setup(app):
    """Custom Sphinx setup."""
    # Add custom CSS/JS processing here (fully implemented example: connect to an event)
    app.add_css_file('custom.css')  # Example: Ensure custom CSS is loaded
    app.add_js_file('custom.js')    # Example: Ensure custom JS is loaded

# -- Suppress warnings ------------------------------------------------------

suppress_warnings = [
    'myst.header',  # Suppress MyST header warnings
    'ref.citation',  # Suppress citation warnings for now
    'app.add_locale',  # Suppress locale warnings
]

# -- Development options -----------------------------------------------------

# Only enable in development
if os.environ.get('SPHINX_DEV'):
    # Enable parallel reading/writing for faster builds
    html_use_opensearch = 'https://allanhanan.github.io/duvc-ctl'
    # Keep going on warnings (for development)
    keep_warnings = True
    # Enable autosummary generation
    autosummary_generate = True
    autosummary_generate_overwrite = True

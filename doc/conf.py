# -*- coding: utf-8 -*-
#
# Heapkeeper documentation build configuration file, created by
# sphinx-quickstart on Sat Mar 28 19:42:44 2009.
#
# This file is execfile()d with the current directory set to its containing
# dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

import sys
import os
import docutils
import re
import string

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.append(os.path.abspath('../src'))

# -- General configuration ----------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = ['sphinx.ext.autodoc']

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The encoding of source files.
source_encoding = 'utf-8'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'Heapkeeper'
copyright = u'2009-2010, Csaba Hoch, Attila Nagy'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = '0.7'
# The full version, including alpha/beta/rc tags.
release = '0.7'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#language = None

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
#today = ''
# Else, today_fmt is used as the format for a strftime call.
#today_fmt = '%B %d, %Y'

# List of documents that shouldn't be included in the build.
#unused_docs = []

# List of directories, relative to source directory, that shouldn't be searched
# for source files.
exclude_trees = ['_build']

# The reST default role (used for this markup: `text`) to use for all
# documents.
#default_role = None

# If true, '()' will be appended to :func: etc. cross-reference text.
#add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
#add_module_names = True

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
#show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# A list of ignored prefixes for module index sorting.
#modindex_common_prefix = []


# -- Options for HTML output --------------------------------------------------

# The theme to use for HTML and HTML Help pages.  Major themes that come with
# Sphinx are currently 'default' and 'sphinxdoc'.
html_theme = 'default'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
html_theme_options = {'nosidebar':'true'}

# Add any paths that contain custom themes here, relative to this directory.
#html_theme_path = []

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
html_title = 'Heapkeeper'

# A shorter title for the navigation bar.  Default is the same as html_title.
#html_short_title = None

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
#html_logo = None

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
html_favicon = 'favicon.ico'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
html_last_updated_fmt = '%Y-%m-%d'

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
#html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
#html_sidebars = {}

# Additional templates that should be rendered to pages, maps page names to
# template names.
#html_additional_pages = {}

# If false, no module index is generated.
#html_use_modindex = True

# If false, no index is generated.
#html_use_index = True

# If true, the index is split into individual pages for each letter.
#html_split_index = False

# If true, links to the reST sources are added to the pages.
#html_show_sourcelink = True

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
#html_use_opensearch = ''

# If nonempty, this is the file name suffix for HTML files (e.g. ".xhtml").
#html_file_suffix = ''

# Output file base name for HTML help builder.
htmlhelp_basename = 'Heapkeeperdoc'


# -- Options for LaTeX output -------------------------------------------------

# The paper size ('letter' or 'a4').
#latex_paper_size = 'letter'

# The font size ('10pt', '11pt' or '12pt').
#latex_font_size = '10pt'

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass
# [howto/manual]).
latex_documents = [
  ('index', 'Heapkeeper.tex', u'Heapkeeper Documentation',
   u'Csaba Hoch, Attila Nagy', 'manual'),
]

# The name of an image file (relative to this directory) to place at the top of
# the title page.
#latex_logo = None

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
#latex_use_parts = False

# Additional stuff for the LaTeX preamble.
#latex_preamble = ''

# Documents to append as an appendix to all manuals.
#latex_appendices = []

# If false, no module index is generated.
#latex_use_modindex = True

# The obfuscation code was taken from
#
#   http://pypi.python.org/pypi/bud.nospam
#
# and was was released by Kevin Teague <kevin at bud ca> under
# a BSD license.

def rot_13_encrypt(line):
    """Rotate 13 encryption.

    """
    line = unicode(line, 'rot_13')
    line = re.sub('(?=[\\"])', r'\\', line)
    line = re.sub('\n', r'\n', line)
    line = re.sub('@', r'\\100', line)
    line = re.sub('\.', r'\\056', line)
    line = re.sub('/', r'\\057', line)
    return line

def js_obfuscated_text(text):
    """ROT 13 encryption with embedded in Javascript code to decrypt
    in the browser.

    """
    return """<script type="text/javascript">document.write(
              "%s".replace(/[a-zA-Z]/g,
              function(c){
                return String.fromCharCode(
                (c<="Z"?90:122)>=(c=c.charCodeAt(0)+13)?c:c-26);}));
                </script>""" % rot_13_encrypt(text)

def js_obfuscated_link(email, displayname=None):
    """ROT 13 encryption within an Anchor tag w/ a mailto: attribute

    """
    if not displayname:
        displayname = email
    return js_obfuscated_text("""<a href="mailto:%s">%s</a>""" % (
        email, displayname
    ))

# -- end bud.nospam

# The following code was taken from Stéfan van der Walt <stefan at sun ac za>,
# who sent it to the Sphinx mailing list:
#
# http://groups.google.com/group/sphinx-dev/browse_thread/thread/c03f6cee47d949ff

def email_role(typ, rawtext, text, lineno, inliner, options={}, content=[]):
    """
    Role to obfuscate e-mail addresses.
    """
    text = text.decode('utf-8').encode('utf-8')
    # Handle addresses of the form "Name <name@domain.org>"
    if '<' in text and '>' in text:
        name, email = text.split('<')
        email = email.split('>')[0]
    else:
        name = text
        email = name

    obfuscated = js_obfuscated_link(email, displayname=name)
    node = docutils.nodes.raw('', obfuscated, format='html')
    return [node], []

# -- end

def setup(app):
    app.add_role('email', email_role)

# This file is part of Heapkeeper.
#
# Heapkeeper is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# Heapkeeper is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# Heapkeeper.  If not, see <http://www.gnu.org/licenses/>.

# Copyright (C) 2009 Csaba Hoch
# Copyright (C) 2009 Attila Nagy

"""|hkcustomlib| is a module that can be used to customize Heapkeeper.

Pseudo-types
''''''''''''

|hkcustomlib| has pseudo-types that are not real Python types, but we use them
as types in the documentation so we can talk about them easily.

.. _hkcustomlib_ShouldPrintDateFun:

- **ShouldPrintDateFun(post, genopts)** -- A function that specifies when to
  print the date of a post in the post summary.

  Real type: fun(|Post|, |GeneratorOptions|) -> bool

.. _hkcustomlib_LocaltimeFun:

- **LocaltimeFun(timestamp)** -- A function that calculates the `tm` structure
  based on a timestamp. This means that it converts global time to local time.

  Real type: fun(int), returns time.tm

.. _hkcustomlib_DateOptions:

- **DateOptions** -- Options on how to handle and show dates.

  Real type: {str: object}

  DateOptions keys:

  - `date_format` (str) -- The format of the date as given to `time.strftime`.
  - `postdb` (|PostDB|) -- The post database to work on.
  - `should_print_date_fun` (|ShouldPrintDateFun|) -- The function that
    specifies when to print-the date of a post in the post summary.
  - `timedelta` (datetime.timedelta) -- A date for the post summary will be
    printed if the time between the post and its parent is less then timedelta.
    (If the post has no parent or the date is not specified in each posts, the
    date is printed.)
  - `localtime_fun` (|LocaltimeFun|) -- A function to be used for calculating
    local time when displaying dates.

  Note: this type should be made into a real class, according to the
  :ref:`Options pattern <options_pattern>`.
"""


import datetime
import os
import subprocess
import time

import hkutils
import hklib
import hkgen


##### Generation #####

def gen_indices(postdb):
    """Generates index pages using the default options.

    **Type:** |GenIndicesFun|
    """

    g = hkgen.Generator(postdb)
    g.write_all()

##### Misc #####

def default_editor():
    """Returns the default editor of the operating system.

    On Unix systems, the default is ``vi``. On Windows, it is ``notepad``.
    On other operating systems, the function returns ``None.``

    **Returns:** str
    """

    if os.name == 'posix':
        return 'vi'
    elif os.name == 'nt':
        return 'notepad'
    else:
        return None

class IncorrectEditorException(hkutils.HkException):

    """Raised when the editor variable is incorrect."""

    def __init__(self, editor, message):
        """Constructor."""
        value = ('Incorrect editor variable:\n'
                 '    %s\n'
                 '%s' % (editor, message))
        super(IncorrectEditorException, self).__init__('Incorrect editor.')

def editor_to_editor_list(editor):
    r"""Converts an editor variable to a list of program name and arguments.

    **Argument:**

    - `editor` (str)

    **Returns:** [str]

    **Examples:** ::

        >>> editor_to_editor_list('gvim')
        ['gvim']
        >>> editor_to_editor_list('vim arg1 arg2')
        ['vim', 'arg1', 'arg2']
        >>> editor_to_editor_list('vim long\\ argument')
        ['vim', 'long argument']
        >>> editor_to_editor_list('vim argument\\\\with\\\\backslash')
        ['vim', 'argument\\with\\backslash']
    """

    editor_list = []
    current_arg = []
    i = 0
    while i < len(editor):
        # If a backslash is found, the next character has to be a space or a
        # backslash, and it should be added to the current argument.
        if editor[i] == '\\':
            if len(editor) <=  i + 1:
                msg = 'Unescaped backslash should not be the final character.'
                raise IncorrectEditorException(editor, msg)
            i += 1
            if editor[i] in [' ', '\\']:
                current_arg.append(editor[i])
            else:
                msg = 'Unexpected character after backslash.'
                raise IncorrectEditorException(editor, msg)
        # If a space is found, a new argument should be started.
        elif editor[i] == ' ':
            if current_arg != []:
                editor_list.append(''.join(current_arg))
                current_arg = []
        # Otherwise the current character has to be added to the current
        # argument.
        else:
            current_arg.append(editor[i])
        i += 1
    if current_arg != []:
        editor_list.append(''.join(current_arg))
        current_arg = []
    return editor_list

def edit_files(files):
    """Opens an editor in which the user edits the given files.

    It invokes the editor program stored in the ``EDITOR`` environment
    variable. If ``EDITOR`` is undefined or empty, it invokes the default
    editor on the system using the :func:`default_editor` function.

    **Type:** |EditFileFun|
    """

    old_content = {}
    for file in files:
        old_content[file] = hkutils.file_to_string(file, return_none=True)

    editor = os.getenv('HEAPKEEPER_EDITOR')

    # if HEAPKEEPER_EDITOR is not set, get EDITOR
    if editor is None or editor == '':
        editor = os.getenv('EDITOR')

    # if EDITOR is not set, get the default editor
    if editor is None or editor == '':
        editor = default_editor()

    # if not even the default is set, print an error message
    if editor is None:
        hklib.log(
           'Cannot determine the default editor based on the operating\n'
           'system. Please set the EDITOR environment variable to the editor\n'
           'you want to use or set hkshell.options.callback.edit_files to\n'
           'call your editor of choice.')
        return False

    try:
        editor = editor_to_editor_list(editor)
    except IncorrectEditorException:
        hklib.log(
            'The editor variable is incorrect:\n' +
            editor +
            'Please set the EDITOR environment variable to the editor\n'
            'you want to use or set hkshell.options.callback.edit_files to\n'
            'call your editor of choice.')
        return False

    subprocess.call(editor + files)

    def did_file_change(file):
        new_content = hkutils.file_to_string(file, return_none=True)
        return old_content[file] != new_content

    changed_files = filter(did_file_change, files)
    return changed_files

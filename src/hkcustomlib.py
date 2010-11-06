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

# Copyright (C) 2009-2010 Csaba Hoch
# Copyright (C) 2009 Attila Nagy

"""|hkcustomlib| is a module that can be used to customize Heapkeeper."""

# TODO This module (and its test module and its documentation module) should be
# removed after releasing v0.9.


import os
import subprocess

import hkutils
import hkgen


##### Generation #####

def gen_indices(postdb):
    """DEPRECATED. Generates index pages using the default options.

    Please use :func:`hkshell.gen_indices` instead.

    **Type:** |GenIndicesFun|
    """

    g = hkgen.Generator(postdb)
    g.write_all()

##### Misc #####

def default_editor():
    """DEPRECATED. Returns the default editor of the operating system.

    Please use :func:`hkshell.default_editor` instead.

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

    """DEPRECATED. Raised when the editor variable is incorrect.

    Please use :class:`hkshell.IncorrectEditorException` instead.
    """

    def __init__(self, editor, message):
        """Constructor."""
        value = ('Incorrect editor variable:\n'
                 '    %s\n'
                 '%s' % (editor, message))
        super(IncorrectEditorException, self).__init__('Incorrect editor.')

def editor_to_editor_list(editor):
    r"""DEPRECATED. Converts an editor variable to a list of program name and
    arguments.

    Please use :func:`hkshell.editor_to_editor_list` instead.

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
    """DEPRECATED. Opens an editor in which the user edits the given files.

    Please use :func:`hkshell.edit_files` instead.

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
        hkutils.log(
           'Cannot determine the default editor based on the operating\n'
           'system. Please set the EDITOR environment variable to the editor\n'
           'you want to use or set hkshell.options.callback.edit_files to\n'
           'call your editor of choice.')
        return False

    try:
        editor = editor_to_editor_list(editor)
    except IncorrectEditorException:
        hkutils.log(
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

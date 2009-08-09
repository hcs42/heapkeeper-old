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

"""Module that can be used to customize the Heap.

Type definitions:
ShouldPrintDateFun -- A function that specifies when to print the date
    of a post in the post summary.
    Real type: fun(post, genopts) -> bool
DateOptions --- Options on how to handle and show dates.
    Real type: dict(str, object)

DateOptions keys:
date_format --- The format of the date as given to time.strftime.
    Type: str
postdb --- The post database to work on.
    Type: str
should_print_date_fun -- The function that specifies when to print the date of
    a post in the post summary.
    Type: ShouldPrintDateFun
timedelta --- A date for the post summary will be printed if the time between
    the post and its parent is less then timedelta. (If the post has no parent
    or the date is not specified in each posts, the date is printed.)
    Type: datetime.timedelta
localtime_fun --- A function that calculates the tm structure based on a
    timestamp.
    Type: (timestamp:int) -> time.tm
"""

import os
import time
import datetime
import hkutils
import hklib
import subprocess

##### Generator #####

def generatoroptions_setdef(options):
    """Sets sensible default options for the given GeneratorOptions object."""
    # Now all options are sensible...
    pass

##### Date #####

def format_date(post, options):
    """Formats the date of the given post.

    If the post does not have a date, the None object is returned.

    Arguments:
    post ---
        Type: Post
    options ---
        Type: DateOptions
        Required options: date_format, localtime_fun

    Returns: str | None
    """

    format = options['date_format']
    localtime_fun = options['localtime_fun']

    timestamp = post.timestamp()
    if timestamp == 0:
        return None
    else:
        return time.strftime(format, localtime_fun(timestamp))

def create_should_print_date_fun(options):
    """Returns a should_print_date_fun.

    Arguments:
    post ---
        Type: Post
    options ---
        Type: DateOptions
        Required options: postdb, timedelta

    Returns: ShouldPrintDateFun
    """

    postdb = options['postdb']
    timedelta = options['timedelta']

    def should_print_date_fun(post, genopts):
        parent = postdb.parent(post)
        if not hasattr(genopts, 'section'):
            return True
        if genopts.section.is_flat:
            return True
        if parent == None:
            return True
        if (post.date() != '' and parent.date() != '' and
            (post.datetime() - parent.datetime() >= timedelta)):
            return True
        return False

    return should_print_date_fun

def create_date_fun(options):
    """Returns a date_fun.

    Arguments:
    options --- DateOptions
        Required options:
            date_format, postdb
            Either postdb, timedelta or should_print_date_fun.

    Returns: hklib.DateFun
    """

    if options['should_print_date_fun'] == None:
        should_print_date_fun = create_should_print_date_fun(options)
    else:
        should_print_date_fun = options['should_print_date_fun']

    def date_fun(post, genopts):
        if should_print_date_fun(post, genopts):
            return format_date(post, options)
        else:
            return None
    return date_fun

def date_defopts(options={}):
    options0 = \
        {'postdb': None,
         'date_format' : '(%Y.%m.%d.)',
         'localtime_fun': time.localtime,
         'should_print_date_fun': None,
         'timedelta': datetime.timedelta(0)}
    options0.update(options)
    return options0

##### Generation #####

def gen_indices(postdb):
    date_options = date_defopts({'postdb': postdb})
    date_fun = create_date_fun(date_options)
    genopts = hklib.GeneratorOptions()
    genopts.postdb = postdb
    section = hklib.Section('', postdb.all())
    genopts.indices = [hklib.Index([section])]
    hklib.Generator(postdb).gen_indices(genopts)

def gen_posts(postdb, posts):
    date_options = date_defopts({'postdb': postdb})
    date_fun = create_date_fun(date_options)
    genopts = hklib.GeneratorOptions()
    genopts.postdb = postdb
    hklib.Generator(postdb).gen_posts(genopts, posts.exp())

def gen_threads(postdb):
    date_options = date_defopts({'postdb': postdb})
    date_fun = create_date_fun(date_options)
    genopts = hklib.GeneratorOptions()
    genopts.postdb = postdb
    genopts.print_thread_of_post = True
    hklib.Generator(postdb).gen_threads(genopts)

##### Misc #####

def default_editor():
    if os.name == 'posix':
        return 'vi'
    elif os.name == 'nt':
        return 'notepad'
    else:
        return None

def edit_file(file):
    """Opens an editor in which the user edits the given file.

    Returns whether the file was changed.

    **Argument:**

    - *file* (str)

    **Returns:** bool
    """

    old_content = hkutils.file_to_string(file, return_none=True)

    editor = os.getenv('EDITOR')

    # if EDITOR is not set, get the default editor
    if editor is None:
        editor = default_editor()

    # if not even the default is set, print an error message
    if editor is None:
        hklib.log(
            'Cannot determine the default editor based on the operating\n'
            'system. Please set the EDITOR environment variable to the editor\n'
            'you want to use or set hkshell.options.callback.edit_file to\n'
            'call your editor of choice.')
        return False

    subprocess.call(editor.split() + [file])
    return hkutils.file_to_string(file, return_none=True) != old_content


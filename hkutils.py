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

"""|hkutils| contains utility functions for Heapkeeper.

Pseudo-types
''''''''''''

|hkutils| has pseudo-types that are not real Python types, but we use them as
types in the documentation so we can talk about them easily.

.. _hkutils_TextStruct:

- **TextStruct** -- A recursive structure that represents a string. A
  |TextStruct| object can be a string, or an iterable object (e.g. list or
  tuple) that contains |TextStruct| objects; i.e. strings or other iterable
  objects. The represented string can be obtained from a |TextStruct| object by
  walking all its leaves and concatenating them.

  The reason for using |TextStruct| objects instead of strings is purely
  efficiency. A |TextStruct| object can be converted to a string using the
  :func:`textstruct_to_str` function, and it can be written into a file object
  using the :func:`write_textstruct` function.

  Examples of |TextStruct| objects:

  - ``'Susan Calvin was born in 1982.'``
  - ``['Susan Calvin ', 'was born ', 'in 1982.']``
  - ``[['Susan ','Calvin '], ('was born ', 'in '), '1982.']``
  - Defining a |TextStruct| called ``iter``::

        def iter():
            yield 'Susan Calvin '
            yield 'was born '
            yield 'in 1982.'

  Real type: str | iterable(|TextStruct|)
"""

from __future__ import with_statement

import datetime
import email.utils
import inspect
import os.path
import shutil
import types


##### Performance measurement #####

pm_last_time = datetime.datetime.now()
pm_action = ''

def int_time(next_action = ''):
    """Returns the time elapsed since the last call of :func:`int_time`."""
    global pm_last_time
    global pm_action
    old_action = pm_action
    pm_action = next_action
    now = datetime.datetime.now()
    delta = now - pm_last_time
    delta = delta.seconds + (delta.microseconds)/1000000.0
    pm_last_time = now
    return old_action, delta

def print_time(next_action = ''):
    """Calls :func:`int_time` and prints the result."""
    old_pm_action, t = int_time(next_action)
    if old_pm_action != '':
        print '%.6f %s' % (t, old_pm_action)
    else:
        print '%.6f' % (t)


##### HkException #####

class HkException(Exception):

    """A very simple exception class used."""

    def __init__(self, value):
        """Constructor.

        **Argument:**

        - `value` (object) -- The reason of the error.
        """
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        """Returns the string representation of the error reason.

        **Returns:** str
        """

        return repr(self.value)


##### Option handling (currently not used) #####

def arginfo(fun):
    """Returns a tuple based on the arguments of the given function.

    The first element of the tuple is the list of arguments that do not have
    a default value. The second element is a dictionary that assigns the
    default values to the arguments that do have a default value.

    **Returns:** ([str], {str: object})
    """

    args, _varargs, _varkw, defaults = inspect.getargspec(fun)
    args_without_default = args[:-len(defaults)]
    argnames_with_default = args[-len(defaults):]
    d = {}
    for argname, argdefault in zip(argnames_with_default, defaults):
        d[argname] = argdefault
    return args_without_default, d

def set_defaultoptions(options, fun, excluded):
    """Reads the options and their default values from the given function's
    argument list and updates the given dictionary accordingly.

    **Arguments:**

    - `options` ({str: object}) -- The dictionary that should be updated with
      the default options.
    - `fun` (fun) -- The list of options and the default options will be read
      from.
    - `excluded` (set(str) | [str]) -- Arguments of 'fun' that are not options
      and should be excluded from the result.
    """

    unused_options = set(options.keys())
    args_without_default, args_with_default = arginfo(fun)
    for optionname in args_without_default:
        if optionname not in excluded:
            if optionname in options:
                unused_options.discard(optionname)
            else:
                raise HkException, \
                      'Option "%s" should be specified in %s' % \
                      (optionname, options)
    for optionname, optiondefault in args_with_default.items():
        if optionname not in excluded:
            options.setdefault(optionname, optiondefault)
            unused_options.discard(optionname)
    if len(unused_options) > 0:
        raise HkException, \
              'Unused options %s in %s' % (list(unused_options), options)


##### Option handling #####

def set_dict_items(obj, d):
    """Sets the items in the dictionary as attributes of the given object.

    If ``'self'`` is included in the dictionary as a key, it will be ignored.
    If `hkutils.NOT_SET` is assigned to the key in the dictionary, that item
    will be ignored.

    **Arguments:**

    - `obj` (object)
    - `d` (dict)
    """

    for var, value in d.items():
        if var != 'self' and value != NOT_SET:
            setattr(obj, var, value)

def check(obj, attributes):
    """Checks that the object does have all the given attributes.

    It throws `AttributeError` if the object does not have one of the
    attributes.

    **Arguments:**

    - `obj` (object)
    - `attributes` ([str])

    **Returns:** ``True``
    """

    for attr in attributes:
        getattr(obj, attr)
    return True


##### TextStruct #####

def textstruct_to_str(text):
    """Convert a text structure to a string.

    **Argument:**

    - `text` (|TextStruct|)

    **Returns:** str

    **Raises:** TypeError
    """

    if isinstance(text, str):
        return text
    else:
        # Could be done more efficiently walking the structure without
        # recursion, and not creating a bunch of temporary structures.
        return ''.join([ textstruct_to_str(item) for item in text ])

def write_textstruct(f, text):
    """Writes a text structure to a file object.

    **Arguments:**

    - `f` (|Writable|)
    - `text` (|TextStruct|)

    **Raises:** TypeError
    """

    if isinstance(text, str):
        f.write(text)
    else:
        for item in text:
            write_textstruct(f, item)

def is_textstruct(text):
    """Returns whether the given object is a |TextStruct|.

    **Arguments:**

    - `text` (object)

    **Returns:** True
    """

    if isinstance(text, str):
        return True
    else:
        try:
            for item in text:
                if not is_textstruct(item):
                    return False
            return True
        except: # pylint: disable-msg=W0702
            return False


##### Misc #####

def file_to_string(file_name, return_none=False):
    """Reads a file's content into a string.

    **Arguments:**

    - `file_name` (str) -- Path to the file.
    - `return_none` (bool) -- Specifies what to do if the file does not exist.
      If `return_none` is ``True``, ``None`` will be returned. Otherwise an
      `IOError` exception will be raised.

    **Returns:** str | ``None``
    """

    if return_none and not os.path.exists(file_name):
        return None
    with open(file_name, 'r') as f:
        s = f.read()
    return s

def string_to_file(s, file_name):
    """Writes a string to a file.

    The old content of the file will be overwritten.

    **Arguments:**

    - `s` (str)
    - `file_name` (str)
    """

    with open(file_name, 'w') as f:
        f.write(s)

def utf8(s, charset):
    """Encodes the given string in the charset into utf-8.

    If the charset is ``None``, the original string will be returned.

    **Arguments:**

    - `s` (str)
    - `charset` (str)
    """

    if charset != None:
        return s.decode(charset).encode('utf-8')
    else:
        return s

def calc_timestamp(date):
    """Calculates a timestamp from a date.

    **Arguments:**

    - `date` (str) -- The date to be converted. It should conform to
      `ref`:`2822`.

    **Returns**: float, which represents an UTC timestamp.

    **Example**::

        >>> hkutils.calc_timestamp("Wed, 20 Aug 2008 17:41:30 +0200")
        1219246890.0
    """

    return email.utils.mktime_tz(email.utils.parsedate_tz(date))

def copy_wo(src, dst):
    """Copy without overwriting.

    If *src* does exist but *dst* does not, the function copies *src* to *dst*.

    **Arguments:**

    - `src` (str) -- The source file.
    - `dst` (str) -- The destination file. It must be the complete target file
      name.

    **Returns:** bool -- ``True`` is copying happened, ``False`` otherwise.
    """

    if not os.path.exists(src):
        return False
    if not os.path.exists(dst):
        shutil.copyfile(src, dst)
        return True
    return False

def plural(n, singular='', plural_ending='s'):
    """Give the appropriate (singular or plural) noun ending for a number.

    Minus one is singular. This decision is based on
    http://en.wiktionary.org/wiki/cardinal_number#Usage_notes

    Can also be used with irregular plurals, just use whole word instead of
    just the ending.

    **Example**::

        >>> print ('%d message%s found.' %
                   (3, hkutils.plural(3)))
        3 messages found.

    **Arguments:**

    - `n` (int) -- The number for which we find the matching ending.
    - `singular` (str) -- The singular ending.
    - `plural_ending` (str) -- The plural ending.

    **Returns**: str
    """

    if n == 1 or n == -1:
        return singular
    else:
        return plural_ending

def add_method(obj, methodname, fun):
    """Adds a new method to the given object.

    **Arguments:**

    - `obj` (object)
    - `methodname` (str)
    - `fun` (function) -- The function that will be added to the object as a
      method. Its first parameter has to be the "self" parameter.
    """

    method = types.MethodType(fun, obj, type(obj))
    setattr(obj, methodname, method)

def insert_sep(seq, separator):
    """Returns a list which is the concatenation of the elements in `seq`.
    `separator` is used as a separator between elements.

    **Arguments:**

    - `seq` (iterable(object))
    - `separator` (object)

    **Returns:** [object]

    **Examples:** ::

        >>> insert_sep([1, 2, 3], 0)
        [1, 0, 2, 0, 3]
        >>> insert_sep([1], 0)
        [1]
        >>> insert_sep([], 0)
        []
    """

    result = []
    first = True
    for item in seq:
        if first:
            first = False
        else:
            result.append(separator)
        result.append(item)
    return result


##### Constants #####

class NOT_SET:
    # "Class has no __init__ method" # pylint: disable-msg=W0232
    # "Too few public methods" # pylint: disable-msg=R0903
    """A totally empty class that is used only as a constant.

    If the value of an option is ``NOT_SET``, is represents that the option is
    not set.
    """

    pass

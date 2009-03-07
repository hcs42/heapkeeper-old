#!/usr/bin/python

from __future__ import with_statement
import datetime
import inspect
import email.utils


##### Performance measurement #####

pm_last_time = datetime.datetime.now()
pm_action = ''
def int_time(next_action = ''):
    """Returns the time elapsed since the last call of int_time."""
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
    """Calls int_time and prints the result."""
    pm_action, t = int_time(next_action)
    if pm_action != '':
        print '%.6f %s' % (t, pm_action)
    else:
        print '%.6f' % (t)


##### HeapException #####

class HeapException(Exception):

    """A very simple exception class used by this module."""

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


##### Option handling (currently not used) #####

def arginfo(fun):
    """Returns a tuple based on the arguments of the given function.
    
    The first element of the tuple is the list of arguments that do not have
    a default value. The second element is a dictionary that assigns the
    default values to the arguments that do have a default value.
    
    Returns: ([str], dict(str, anything))
    """

    args, varargs, varkw, defaults = inspect.getargspec(fun)
    args_without_default = args[:-len(defaults)]
    argnames_with_default = args[-len(defaults):]
    d = {}
    for argname, argdefault in zip(argnames_with_default, defaults):
        d[argname] = argdefault
    return args_without_default, d

def set_defaultoptions(options, fun, excluded):
    """Reads the options and their default values from the given function's
    argument list and updates the given dictionary accordingly.

    Arguments:
    options --- The dictionary that should be updated with the default options.
        Type: dict(str, anything)
    fun --- The list of options and the default options will be read from
        this function.
        Type: function
    excluded --- Arguments of 'fun' that are not options and should be
        excluded from the result.
        Type: set(str) | [str]
    """

    unused_options = set(options.keys())
    args_without_default, args_with_default = arginfo(fun)
    for optionname in args_without_default:
        if optionname not in excluded:
            if optionname in options:
                unused_options.discard(optionname)
            else:
                raise HeapException, \
                      'Option "%s" should be specified in %s' % \
                      (optionname, options)
    for optionname, optiondefault in args_with_default.items():
        if optionname not in excluded:
            options.setdefault(optionname, optiondefault)
            unused_options.discard(optionname)
    if len(unused_options) > 0:
        raise HeapException, \
              'Unused options %s in %s' % (list(unused_options), options)

##### Option handling #####

def set_dict_items(object, dict):
    """Sets the items in the dictionary as attributes of the given object.

    If 'self' is included in the dictionary as a key, it will be ignored.

    Arguments:
    object --
        Type: object
    dict --
        Type: dict
    """

    for var, value in dict.items():
        if var != 'self':
            setattr(object, var, value)


##### Misc #####

def file_to_string(file_name):
    """Reads a file's content into a string."""

    with open(file_name, 'r') as f:
        s = f.read()
    return s

def string_to_file(s, file_name):
    """Writes a string to a file."""
    with open(file_name, 'w') as f:
        f.write(s)

def utf8(s, charset):
    """Encodes the given string in the charset into utf-8.

    If the charset is None, the original string will be returned.
    """
    if charset != None:
        return s.decode(charset).encode('utf-8')
    else:
        return s

def calc_timestamp(date):
    """Calculates a timestamp from a date.

    The date argument should conform to RFC 2822.
    The timestamp will be an UTC timestamp.
    """
    return email.utils.mktime_tz(email.utils.parsedate_tz(date))

##### Constants #####

class NOT_SET: pass

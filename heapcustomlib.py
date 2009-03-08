#!/usr/bin/python

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
maildb --- The mail database to work on.
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

import time
import datetime
import heapmanip

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
        Required options: maildb, timedelta

    Returns: ShouldPrintDateFun
    """

    maildb = options['maildb']
    timedelta = options['timedelta']

    def should_print_date_fun(post, genopts):
        prev = maildb.prev(post)
        if genopts.section.is_flat:
            return True
        if prev == None:
            return True
        if (post.date() != '' and prev.date() != '' and
            (post.datetime() - prev.datetime() >= timedelta)):
            return True
        return False

    return should_print_date_fun

def create_date_fun(options):
    """Returns a date_fun.

    Arguments:
    options --- DateOptions
        Required options:
            date_format, maildb
            Either maildb, timedelta or should_print_date_fun.

    Returns: heapmanip.DateFun
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
        {'maildb': None,
         'date_format' : '(%Y.%m.%d.)',
         'localtime_fun': time.localtime,
         'should_print_date_fun': None,
         'timedelta': datetime.timedelta(0)}
    options0.update(options)
    return options0

def gen_indices(maildb):
    date_options = date_defopts({'maildb': maildb})
    date_fun = create_date_fun(date_options)
    genopts = heapmanip.GeneratorOptions()
    genopts.maildb = maildb
    section = heapmanip.Section(maildb.all())
    genopts.indices = [heapmanip.Index([section])]
    heapmanip.Generator(maildb).gen_indices(genopts)

def gen_posts(maildb):
    date_options = date_defopts({'maildb': maildb})
    date_fun = create_date_fun(date_options)
    genopts = heapmanip.GeneratorOptions()
    genopts.maildb = maildb
    heapmanip.Generator(maildb).gen_posts(genopts)

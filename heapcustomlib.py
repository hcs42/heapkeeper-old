"""
Type definitions:

should_print_date_fun -- A function that specifies when to print the date
    of a post in the post summary.
    Real type: (post) -> bool

DateFunOptions:

date_format --- The format of the date as given to time.strftime.
    Type: str
maildb --- The mail database to work on.
    Type: str
should_print_date_fun -- The function that specifies when to print the date of
    a post in the post summary.
    Type: should_print_date_fun
timedelta --- A date for the post summary will be printed if the time between
    the post and its parent is less then timedelta. (If the post has no parent
    or the date is not specified in each posts, the date is printed.)
    Type: datetime.timedelta
localtime_fun --- A 
    Type: (timestamp:int) -> time.tm
"""

import time
import datetime
import heapmanip

##### Generator #####

def generator_defopts(options={}):
    """Returns sensible default options for the methods of
    heapmanip.Generator"""
    
    options0 = \
        {'sections': None,
         'write_toc': True,
         'write_date': True,
         'shortsubject': False,
         'shorttags': False,
         'date_fun': None,
         'html_title': 'Heap index',
         'html_h1': 'Heap index',
         'cssfile': 'heapindex.css'}
    options0.update(options)
    return options0

##### Date #####

def format_date(post, options):
    """Formats the date of the given post.

    If the post does not have a date, the None object is returned.

    Arguments:
    post ---
        Type: Post
    options ---
        Type: DateFunOptions
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
        Type: DateFunOptions
        Required options: maildb, timedelta

    Returns: should_print_date_fun
    """

    maildb = options['maildb']
    timedelta = options['timedelta']

    def should_print_date_fun(post, section):
        prev = maildb.prev(post)
        if section[2]['flat']:
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
    options --- DateFunOptions
        Required options:
            date_format, maildb
            Either maildb, timedelta or should_print_date_fun.

    Returns: date_fun
    """

    if options['should_print_date_fun'] == None:
        should_print_date_fun = create_should_print_date_fun(options)
    else:
        should_print_date_fun = options['should_print_date_fun']

    def date_fun(post, section):
        if should_print_date_fun(post, section):
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
         'timedelta': datetime.timedelta(days=5)}
    options0.update(options)
    return options0

#!/usr/bin/python

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

"""Heapkeeper's interactive shell.

The interactive shell defines commands that are actually Python functions in
the :mod:`hkshell` module. These functions perform high-level manipulaton on
the heap, and they tend to have very short names.

To get help after from within hkshell, type ``h()``. It will print the list of
features and commands with a short description.

Invocation
''''''''''

Using the ``hkshell`` sh script (not ``hkshell.py``) to start the ``hkshell``
is more convenient than using ``hkshell directly.``

The reason is the following. When :mod:`hkshell` is invoked, the user usually
wants to have a Python shell which has the hkshell commands defined. If
:mod:`hkshell` is invoked by simply typing ``python hkshell.py``, the Python
interpreter will exit after sourcing :mod:`hkshell`. In order to stop the
Python interpreter from exitig, the ``python`` command has to be augmented with
a ``-i`` option. That is exactly what the ``hkshell`` script does: it forwards
all its arguments to :mod:`hkshell` and calls it with ``python -i``. If there
is no sh shell on the system or a Python version different from the one that is
executed when calling ``python`` is wanted to be used, the :mod:`hkshell`
module can be called directly in the same way as the ``hkshell`` script does.

**Command line arguments:**

The ``hkshell`` script and the :mod:`hkshell` module have the same command line
arguments. There is no mandatory argument, only options. The options are the
following:

- ``-h``, ``--help`` --
  hkshell shows a help message and exits.
- ``-b <before_command>``, ``--before <before_command>`` --
  Python code to execute before importing hkrc. Any number of before commands
  may be specified.
- ``-c <after_command>``, ``--command <after_command>`` --
  Python code to execute after importing hkrc. Any number of after commands may
  be specified.
- ``-r <hkrc>``, ``--hkrc <hkrc>`` --
  Modules to import as hkrc modules. Any number of modules may be specified. If
  nothing is specified, the ``hkrc`` module is imported. If ``NONE`` is
  specified, nothing is imported. If a module is not found, the program gives
  only a warning.
- ``--configfile <configfile>`` --
  The name of the Heapkeeper config file to use.

The ``--hkrc`` option deals with the modules that should be imported when
hkshell is started. The convention (and the default behaviour) is that there is
a module called ``hkrc`` which is imported. The ``hkrc`` module customizes the
tool to the user's needs.

**Examples:**

.. highlight:: sh

Starting hkshell from the script::

    $ ./hkshell

The same, using custom Python version::

    $ /home/my/bin/python -i hkshell.py

This example downloads new emails, generates the index pages and exits after
saving the post database::

    $ ./hkshell -c 'dl()' -c 'g()' -c 'x()'

Positional arguments
::::::::::::::::::::

Currently the ``-c`` markers may be omitted and the positional arguments (the
ones without ``-<character>`` and ``--<word>``) will be executed as commands::

    $ ./hkshell 'dl()' 'g()' 'x()'

Do not write this in scripts that you want to keep, because this behaviour may
be changed in the future if we want to use positional arguments for something
else.

Initialization
''''''''''''''

The following actions are performed when hkshell starts:

1. The commands after the ``--before`` options are executed.
2. The ``hk.cfg`` configuration file and the post database are read.
3. The default event handlers are set.
4. The ``hkrc`` file(s) are executed.
5. The commands after the ``--after`` options are executed.

Usage
'''''

After performing the initial tasks, the Python interpreter is left open. The
functions of :mod:`hkshell` are imported, so they can be used without having to
write ``hkshell.``. These functions are called commands. The user can define
own commands, as well. For reading about the commands of :mod:`hkshell`, type
``h()`` if you are in the hkshell, or go to the :ref:`hkshell_commands` section
if you are reading the documentation.

**Type definitions:**

:mod:`hkshell` has pseudo-types that are not real Python types, but we use them
as types in the documentation so we can talk about them easily.

.. _hkshell_PrePost:

- *PrePost* (heapid | int | |Post|) -- An object that can be converted into
  a |Post|. When it is an *int*, it will be converted to a string that should
  represent a heapid. The *heapid* is converted to a |Post| based on the post
  database.

.. _hkshell_PrePostSet:

- *PrePostSet* (set(|PrePost|)) | [|PrePost|] | |PrePost| | |PostSet|) -- An
  object that can be converted into a |PostSet|. Actually, |PrePostSet| can be
  any iterable object that iterates over |PrePost| objects.

.. _hkshell_Tag:

- *Tag* (str) -- A tag.

.. _hkshell_PreTagSet:

- *PreTagSet* (|Tag| | set(|Tag|) | [|Tag|]) -- An object that can be converted
  into a set of tags.

**Features**

:mod:`hkshell` has a concept of features. A feature can be turned on and off.
For the list of features, see :func:`on`.

.. highlight:: python
"""

console_help = """\
Types
-----

pp = PrePost = int | str | Post
pps = PrePostSet = prepost | [prepost] | set(prepost) | PostSet
pts = PreTagSet = tag | set(tag) | [tag]

Features
--------

gen_indices        - automatically regenerates the index pages
gen_posts          - automatically regenerates the post pages after 
save               - automatically saves the post database after commands
timer              - times the commands
touched_post_printer - prints touched posts
event_printer      - prints all events

Commands
--------

h()                - prints a detailed help
hh()               - print help about the commands
s()                - save
x()                - save and exit
rl()               - reload the database (changes will be lost!)
g()                - generate index.html
ga()               - generate all html
gs()               - generate index.html and save
ps(pps)            - create a postset
ls(ps)             - get a summary of a postset

pt(pps)            - propagate tags
at(pps, pts)       - add tag/tags
atr(pps, pts)      - add tag/tags recursively
rt(pps, pts)       - remove tag/tags
rtr(pps, pts)      - remove tag/tags recursively
st(pps, pts)       - set tag/tags
str_(pps, pts)     - set tag/tags recursively

pS(pps)            - propagate subject
sS(pps, subj)      - set subject
sSr(pps, subj)     - set subject recursively
cS(pps, subj)      - capitalize the subject
cSr(pps, subj)     - capitalize the subject recursively

d(pps)             - delete
dr(pps)            - delete recursively
j(pp, pp)          - join two threads
e(pp)              - edit the post as a file
dl()               - download new mail

postdb()           - the post database object
c()                - shorthand for postdb().all().collect
on(feature)        - turning a feature on
off(feature)       - turning a feature off

For further help on a command type ``help(<command name>)`` or see the HTML
documentation.
"""


import sys
import time
import subprocess
import ConfigParser
import re
import optparse
import inspect
from functools import wraps

import hkutils
import hklib
import hkcustomlib


##### Callbacks #####

class Callbacks(object):
    """Stores callback functions or objects that are used by :mod:`hkshell`.
    
    The attributes are mentioned as functions, but they can be objects with
    *__call__* method, as well.

    **Attributes:**

    - *gen_indices* (fun(|PostDB|)) -- Function that generates indices.
    - *gen_posts* (fun(|PostDB|)) -- Function that generates the HTML files of
      the posts.
    - *edit_file* (fun(str) -> bool) -- Function that opens an editor with the
      given file. It should return ``True`` or ``False`` when the user finished
      editing the file. If the changed file should be taken into account, it
      should return ``True``, otherwise ``False``.
    """

    def __init__(self,
                 gen_indices=hkcustomlib.gen_indices,
                 gen_posts=hkcustomlib.gen_posts,
                 edit_file=hkcustomlib.edit_file):

        super(Callbacks, self).__init__()
        hkutils.set_dict_items(self, locals())


##### Options #####

class Options(object):
    """Represents a hkshell option object.

    **Attributes:**

    - *config* (ConfigParser.ConfigParser) -- Configuration object.
    - *output* (object) -- When a hkshell function wants to print something, it
      calls *output*'s write method.
      Default value: sys.stdout
    - *callbacks* (:class:`Callbacks`)
    """

    def __init__(self,
                 postdb=hkutils.NOT_SET,
                 config=hkutils.NOT_SET,
                 output=sys.stdout,
                 callbacks=hkutils.NOT_SET):

        super(Options, self).__init__()
        hkutils.set_dict_items(self, locals())

options = Options(callbacks=Callbacks())


##### Event handling #####

class Event(object):
    """Represents an event.

    Data attributes:
    TODO
    """

    def __init__(self,
                 type,
                 command=None,
                 postset=None):

        super(Event, self).__init__()
        hkutils.set_dict_items(self, locals())

    def __str__(self):
        s = '<Event with the following attributes:'
        for attr in ['type', 'command', 'postset']:
            s += '\n%s = %s' % (attr, getattr(self, attr))
        s += '>'
        return s

listeners = []

def append_listener(listener):
    if listener not in listeners:
        listeners.append(listener)
    else:
        raise hkutils.HkException, \
              'Listener already among listeners: %s' % (listener,)

def remove_listener(listener):
    if listener not in listeners:
        raise hkutils.HkException, \
              'Listener not among listeners: %s' % (listener,)
    else:
        listeners.remove(listener)

def event(*args, **kw):
    e = Event(*args, **kw)
    for fun in listeners:
        fun(e)

def hkshell_events(command=None):
    """This function is a decorator that raises events before and after the
    execution of the decorated function.

    **Arguments:**

    - *command* (str) -- The ``command`` attribute of the event that should
      be raised. If ``None``, the name of the function will be used as the
      command name. The default value is ``None``.

    Example::

        @hkshell_events()
        def s():
            postdb().save()
    """

    def inner(f):
        command2 = f.__name__ if command == None else command
        @wraps(f)
        def inner2(*args, **kw):
            event('before', command=command2)
            result = f(*args, **kw)
            event('after', command=command2)
            return result
        return inner2
    return inner


def postset_operation(operation):
    '''This function is a decorator to be used for decorating commands that
    manipulate posts based on a given postset.

    The decorated function will perform the following steps when invoked:

    1. Raises ``event('before', command)``.
    2. Calculates the postset to operate on. This will be referred as the
       ``posts`` variable.
    3. Raises ``event('postset_calculated', command, postset=posts)``.
    4. If ``posts`` is not an empty set, invokes the original command with
       ``posts`` as a first formal parameter and the other actual parameters as
       other formal parameters.
    5. Raises ``event('after', command, postset=posts)``.

    Example on how to define a function that is decorated with
    *postset_operation*::

        @postset_operation
        def d(posts):
            """Deletes the posts in *pps*.
            
            **Arguments:**

            - *pps* (``PrePostSet``)
            """

            posts.forall.delete()

    Note that the first (and only) parameter of the original function is
    *posts*, but the the first parameter of the decorated function is *pps*!
    That is why the documentation of :func:`d` states that the name of the
    parameter is *pps*.

    A more complex example::

        @postset_operation
        def add_tags_recursively(posts, tags):
            tags = tagset(tags)
            for p in posts.expf():
                p.set_tags(tags.union(p.tags()))
    '''

    @wraps(operation)
    def inner(pps, *args, **kw):
        command = operation.__name__
        event('before', command)
        posts = ps(pps)
        event('postset_calculated', command, postset=posts)
        if len(posts) != 0:
            operation(posts, *args, **kw)
        event('after', command, postset=posts)
    return inner

##### Listeners #####

class ModificationListener(object):
    
    """TODO"""
    
    def __init__(self, postdb_arg=None):
        super(ModificationListener, self).__init__()
        self._postdb = postdb_arg if postdb_arg != None else postdb()
        self._postdb.listeners.append(self)
        self._posts = self._postdb.postset([])

    def close(self):
        self._postdb.listeners.remove(self)

    def __call__(self, e):
        if e.type == 'before':
            self._posts = self._postdb.postset([])
        elif isinstance(e, hklib.PostDBEvent) and e.type == 'touch':
            self._posts.add(e.post)

    def touched_posts(self):
        return self._posts


def gen_indices_listener(e):
    if (e.type == 'after' and len(modification_listener.touched_posts()) > 0):
        gen_indices()

def gen_posts_listener(e):
    if e.type == 'after':
        touched_posts = modification_listener.touched_posts()
        if len(touched_posts) > 0:
            gen_posts(touched_posts)

def save_listener(e):
    if (e.type == 'after' and len(modification_listener.touched_posts()) > 0):
        postdb().save()
        write('Mail database saved.\n')

def timer_listener(e, start=[None]):
    if e.type == 'before':
        start[0] = time.time()
    elif e.type == 'after':
        write('%f seconds.\n' % (time.time() - start[0],))

def event_printer_listener(e):
    """Prints the event."""
    write('%s\n' % (e,))


class TouchedPostPrinterListener(object):

    def __init__(self, commands):
        super(TouchedPostPrinterListener, self).__init__()
        self.commands = commands
        self.command = None
        
    def __call__(self, e):
        if e.type == 'before':
            self.command = e.command
        elif e.type == 'after' and self.command in self.commands:
            touched_posts = modification_listener.touched_posts()
            if len(touched_posts) == 0:
                write('No post has been touched.\n')
            else:
                if len(touched_posts) == 1:
                    write('1 post has been touched:\n')
                else:
                    write('%s posts have been touched:\n' % 
                          (len(touched_posts),))
                write('%s\n' %
                      [ post.heapid() for post in touched_posts.sorted_list()])

# Commands after which the touched_post_printer should print the touched posts
touching_commands = \
    ['d', 'dr', 'j', 'pt', 'at', 'atr', 'rt', 'rtr', 'st', 'str_', 'pS', 'sS',
     'sSr', 'capitalize_subject', 'cS', 'cSr']

touched_post_printer_listener = TouchedPostPrinterListener(touching_commands)


##### Features #####

def set_listener_feature(listener, state):
    """Sets the given listener feature to the given state."""
    if state == 'on':
        try:
            append_listener(listener)
        except hkutils.HkException:
            write('Feature already set.\n')
    else: # state == 'off'
        try:
            remove_listener(listener)
        except hkutils.HkException:
            write('Feature not set.\n')

def get_listener_feature(listener):
    """Returns whether the given listener feature is turned on."""
    if listener in listeners:
        return 'on'
    else:
        return 'off'

def set_feature(state, feature):
    if feature in ['gi', 'gen_indices']:
        set_listener_feature(gen_indices_listener, state)
    elif feature in ['gp', 'gen_posts']:
        set_listener_feature(gen_posts_listener, state)
    elif feature in ['s', 'save']:
        set_listener_feature(save_listener, state)
    elif feature in ['t', 'timer']:
        set_listener_feature(timer_listener, state)
    elif feature in ['tpp', 'touched_post_printer']:
        set_listener_feature(touched_post_printer_listener, state)
    elif feature in ['ep', 'event_printer']:
        set_listener_feature(event_printer_listener, state)
    else:
        write('Unknown feature.\n')

def features():
    g = get_listener_feature
    return {'gen_indices': g(gen_indices_listener),
            'gen_posts': g(gen_posts_listener),
            'save': g(save_listener),
            'timer': g(timer_listener),
            'touched_post_printer': g(touched_post_printer_listener)}

def on(feature):
    """Sets a feature to on.

    **Argument:**

    - feature (str)

    **Features:**
    
    All features have a long and a short name.

    - *gi*, *gen_indices* -- Automatically regenerates the index pages.
    - *gp*, *gen_posts* -- Automatically regenerates the post pages after .
    - *s*, *save* -- Automatically saves the post database after commands.
    - *t*, *timer* -- Times the commands.
    - *tpp*, *touched_post_printer* -- Prints touched posts.
    - *ep*, *event_printer* -- Prints all events.
    """

    set_feature('on', feature)

def off(feature):
    """Sets a feature to off.

    See the possible features in the documentation of the :func:`on` function.

    **Argument:**

    - feature (str)
    """

    set_feature('off', feature)


##### Generic functionality #####

def write(str):
    options.output.write(str)

def postdb():
    return options.postdb

def c():
    return postdb().all().collect

def gen_indices():
    options.callbacks.gen_indices(postdb())

def gen_posts(posts=None):
    # TODO: add arguments about the posts to gen_posts()
    #
    # The following line will be replaced with this line:
    # options.callbacks.gen_posts(postdb(), posts)
    options.callbacks.gen_posts(postdb())

def ps(pps):
    res = postdb().postset(pps)
    return res

def tagset(tags):
    """Converts the argument to ``set(tag)``.
    
    **Arguments:**
    - tags (|PreTagSet|)

    **Returns:** set(|Tag|)
    """

    if isinstance(tags, set):
        return tags
    elif isinstance(tags, str):
        return set([tags])
    elif isinstance(tags, list):
        return set(tags)
    else:
        raise hkutils.HkException, \
              'Cannot convert object to tagset: %s' % (tags,)

##### Commands #####

def h():
    """Prints the console help."""
    write(console_help)

@hkshell_events()
def s():
    """Saves the post database."""
    postdb().save()

def x():
    """Saves the post database and exits."""

    event('before', 'x')
    postdb().save()
    event('after', 'x')
    sys.exit()

def q():
    """Exits without saving the post database."""

    event('before', 'q')
    event('after', 'q')
    sys.exit()

@hkshell_events()
def rl():
    """Reloads the post from the disk.

    Changes that have not been saved (e.g. with the :func:`s` command) will
    be lost.
    """

    postdb().reload()

@hkshell_events()
def g():
    """Generates the index pages."""
    gen_indices()

@hkshell_events()
def ga():
    """Generates the index and post pages."""
    gen_indices()
    gen_posts()

@hkshell_events()
def ls(pps):
    """Lists the content of the given postset.
    
    **Arguments:**

    - *ps* (|PrePostSet|)
    """
    for p in ps(pps):
        sum = p.subject() if len(p.subject()) < 40 \
            else p.subject()[:37] + '...'
        write('%s %s %s\n' % (p.author(), p.date(), sum))

@postset_operation
def d(posts):
    """Deletes the posts in *pps*.
    
    **Argument:**

    - *pps* (|PrePostSet|)
    """

    posts.forall.delete()

@postset_operation
def dr(posts):
    """Deletes the posts in *pps* and all their children.

    **Argument:**

    - *pps* (|PrePostSet|)
    """

    posts.expf().forall.delete()

@hkshell_events()
def j(pp1, pp2):
    """Joins two posts.

    Arguments:

    - *pp1* (|PrePost|) -- The post that will be the parent.
    - *pp2* (|PrePost|) -- The post that will be the child.
    """

    p1 = postdb().post(pp1)
    p2 = postdb().post(pp2)
    event('postset_calculated', 'j')
    if p1 != None and p2 != None:
        p2.set_parent(p1.heapid())

@hkshell_events()
def e(pp):
    """Edits a post.

    **Argument:**

    - *pp* (|PrePost|)
    """

    p = postdb().post(pp)
    if p != None:
        postdb().save()
        result = options.callbacks.edit_file(p.postfilename())
        if result == True:
            p.load()
    else:
        hklib.log('Post not found.')

@hkshell_events()
def dl(from_=0):
    """Downloads new posts from an IMAP server.
    
    **Argument:**

    - *from_* (int): the messages whose index in the INBOX is lower than
      this parameter will not be downloaded.
    """

    email_downloader = hklib.EmailDownloader(postdb(), options.config)
    email_downloader.connect()
    email_downloader.download_new(int(from_))
    email_downloader.close()


##### Commands / tags #####

@postset_operation
def pt(posts):
    """Propagates the tags of the posts in *pps* to all their children.
    
    **Argument:**

    - *pps* (|PrePostSet|)
    """

    for post in posts:
        def add_tags(p):
            for tag in post.tags():
                p.add_tag(tag)
        postdb().postset(post).expf().forall(add_tags)

@postset_operation
def at(posts, tags):
    """Adds the given tags to the posts in *pps*.
    
    **Arguments:**

    - *pps* (|PrePostSet|)
    - *tags* (|PreTagSet|) -- Tags to be added.
    """

    tags = tagset(tags)
    for p in posts:
        p.set_tags(tags.union(p.tags()))

@postset_operation
def atr(posts, tags):
    """Adds the given tags to the posts of the given postset and all their
    children.

    **Arguments:**

    - *pps* (|PrePostSet|)
    - *tags* (|PreTagSet|) -- Tags to be added.
    """

    tags = tagset(tags)
    for p in posts.expf():
        p.set_tags(tags.union(p.tags()))

@postset_operation
def rt(posts, tags):
    """Removes the given tags from the posts in *pps*.
    
    **Arguments:**

    - *pps* (|PrePostSet|)
    - *tags* (|PreTagSet|) -- Tags to be removed.
    """

    tags = tagset(tags)
    for p in posts:
        p.set_tags(set(p.tags()) - tags)

@postset_operation
def rtr(posts, tags):
    """Removes the given tags from the posts in *pps* and from all their
    children.

    **Arguments:**

    - *pps* (|PrePostSet|)
    - *tags* (|PreTagSet|) -- Tags to be removed.
    """

    tags = tagset(tags)
    for p in posts.expf():
        p.set_tags(set(p.tags()) - tags)

@postset_operation
def st(posts, tags):
    """Sets the given tags on the posts in *pps*.
    
    **Arguments:**

    - *pps* (|PrePostSet|)
    - *tags* (|PreTagSet|) -- Tags to be set.
    """

    tags = tagset(tags)
    for p in posts:
        p.set_tags(tags)

@postset_operation
def str_(posts, tags):
    """Sets the given tags on the posts in *pps* and on all their children.

    **Arguments:**

    - *pps* (|PrePostSet|)
    - *tags* (|PreTagSet|) -- Tags to be set.
    """

    tags = tagset(tags)
    for p in posts.expf():
        p.set_tags(tags)


##### Commands / subject #####

@postset_operation
def pS(posts):
    """Propagates the subject of the posts in *pps* and all their children.
    
    **Argument:**

    - *pps* (|PrePostSet|)
    """

    for post in posts:
        postdb().postset(post).expf().forall.set_subject(post.subject())

@postset_operation
def sS(posts, subject):
    """Sets the given subject for the posts in *pps*.
    
    **Arguments:**

    - *pps* (|PrePostSet|)
    - *subject* (str) - Subject to be set.
    """

    posts.forall.set_subject(subject)

@postset_operation
def sSr(posts, subject):
    """Sets the given subject for the posts in *pps* and for all their
    children.

    **Arguments:**

    - pps (|PrePostSet|)
    - subject (str) - Subject to be set.
    """

    posts.expf().forall.set_subject(subject)

def capitalize_subject(post):
    """Capitalizes the subject of *post*

    **Arguments:**

    - post (|Post|)
    """

    post.set_subject(post.subject().capitalize())

@postset_operation
def cS(posts):
    """Capitalizes the subject of the posts in *pps*.
    
    **Arguments:**

    - *pps* (|PrePostSet|)
    """

    posts.forall(capitalize_subject)

@postset_operation
def cSr(posts):
    """Capitalizes the subject of the posts in *pps* and all their children.

    **Argument:**

    - *pps* (|PrePostSet|)
    """

    posts.expf().forall(capitalize_subject)


## Utility functions for user-defined commands

def shell_cmd(f):
    """This function is a decorator that defines the decorated function as a
    hkshell command.
    
    Defining a hkshell commands means that *f* can be used from hkshell without
    specifying in which module it is. It also can be used after the
    ``--commands`` argument of hkshell.

    One of the important uses of this decorator is to decorate functions in the
    ``hkrc`` module that the user wants to use conveniently. As an example,
    let's suppose ``hkrc.py`` contains this code::

        @hkshell.shell_cmd
        def mycmd():
            print 'Hi, this is my command.'

    The *mycmd* function can be used from the hkshell as a normal hkshell command::

        >>> mycmd()
        Hi, this is my command.
        >>> 
    """

    define_cmd(f.__name__, f)
    return f

# Stores the commands defined by the user.
user_commands = {}

def define_cmd(name, fun):
    """Defines a hkshell command.
    
    Defining a hkshell commands means that :func:`define_cmd` manipulates its
    environment in such a way that *fun* can be used from hkshell without
    specifying in which module it is, and just invoking it by its *name*.

    **Arguments:**

    - *name* (str): The name by which the command can be invoked, i.e. the
      name to which the function should be bound.
    - *fun* (fun(\*args, \*\*kw)): An arbitrary function. This will be called
      when the command is invoked.
    """

    # This command is a hack.

    # It find the outmost frame, which belongs to the interpreter itself and
    # defines the command there.
    frame = inspect.getouterframes(inspect.currentframe())[-1][0]
    frame.f_globals[name] = fun

    # It defines the command in the user_commands dictionary, which is used by
    # the exec_commands function to specify the global variables.
    user_commands[name] = fun


##### Main #####

def exec_commands(commands):
    """Executes the given commands.
    
    **Argument:**

    - *commands* ([str])
    """

    globals2 = globals().copy()
    globals2.update(user_commands)
    for command in commands:
        exec command in (globals2)

def read_postdb(configfile):
    """Reads the config file and the post database from the disk.
    
    **Argument:**

    - *configfile* (str) -- The name of the config file to use as ``hk.cfg``.

    **Returns:** (ConfigParser, |PostDB|)
    """

    config = ConfigParser.ConfigParser()
    try:
        config.readfp(open(configfile))
    except IOError:
        hklib.log('Config file not found: "%s"' % (configfile,))
        sys.exit(1)
    return config, hklib.PostDB.from_config(config)

def init():
    """Sets the default event handlers."""
    global modification_listener
    modification_listener = ModificationListener(postdb())
    listeners.append(modification_listener)

def import_module(modname):
    """Imports the *modname* module.

    It prints whether it succeeded or not using :func:`hklib.log`.

    **Argument:**

    - *modname* (str)
    """

    try:
        hklib.log('Importing %s...' % (modname,))
        __import__(modname)
        hklib.log('Importing %s OK' % (modname,))
    except ImportError:
        hklib.log('Module not found: "%s"' % (modname,))

def main(cmdl_options, args):
    """Initializes the hkshell.
    
    It performs the following steps:

    1. Executes the "before" commands.
    2. Reads the configuration file and the post database.
    3. Sets the default event handlers.
    4. Executes the hkrc file(s).
    5. Executes the "after" commands.

    **Arguments:**

    - *cmdl_options* (dict(str, [str])): Command line options.
    - *args* ([str]): Command line arguments.
    """

    # Processing the command line options
    cmdl_options.after_command += args

    if cmdl_options.hkrc == []:
        to_import = ['hkrc']
    elif cmdl_options.hkrc == ['NONE']:
        to_import = []
    else:
        to_import = cmdl_options.hkrc

    # Executing "before" commands
    exec_commands(cmdl_options.before_command)

    # Reading the configuration file and the post database.
    options.config, options.postdb = read_postdb(cmdl_options.configfile)

    # Init
    init()

    # Importing modules
    for modname in to_import:
        import_module(modname)

    # Executing "after" commands
    exec_commands(cmdl_options.after_command)


# See more in hkshell's developer documentation (in the HTML documentation or
# in doc/hkshell.rst) on what happens the hkshell is invoked.

if __name__ == '__main__':

    # Parsing the command line options

    parser = optparse.OptionParser()

    # Note: dest='before_commands' would be more logical than
    # dest='before_command' since it is a list; but the help text is more
    # sensible this way.
    parser.add_option('-b', '--before', dest='before_command',
                      help='Python code to execute before importing hkrc',
                      action='append', default=[])
    parser.add_option('-c', '--command', dest='after_command',
                      help='Python code to execute after importing hkrc',
                      action='append', default=[])
    parser.add_option('-r', '--hkrc', dest='hkrc',
                      help='Modules to import',
                      action='append', default=[])
    parser.add_option('--configfile', dest='configfile',
                      help='Configfile to use',
                      action='store', default='hk.cfg')
    (cmdl_options, args) = parser.parse_args()

    from hkshell import *
    main(cmdl_options, args)


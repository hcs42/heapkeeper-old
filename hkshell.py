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
the hkshell module. These functions do high-level manipulaton on the heap, and
they tend to have very short names.

To get help after from within hkshell, type ``h()``. It will print the list of
features and commands with a short description.

**Type definitions:**

- ``PrePost`` (``heapid | int |`` :class:`hklib.Post`) -- An object that can be
  converted into a :class:`hklib.Post`. When it is an ``int``, it will be
  converted to a string that should represent a heapid. The ``heapid`` is
  converted to a :class:`hklib.Post` based on the post database.
- ``PrePostSet`` (``set(PrePost) | [PrePost] | PrePost |``
  :class:`hklib.PostSet`) -- An object that can be converted into a
  :class:`hklib.PostSet`. Actually, ``PrePostSet`` can be any iterable object
  that iterates over ``PrePost`` objects.
- ``Tag`` (``str``) -- A tag.
- ``PreTagSet`` (``Tag | set(Tag) | [Tag]``) -- An object that can be converted
  into a tagset.

**Arguments of hkshell**

Arguments given to the :mod:`hkshell` from the command line will be evaluated
as commands.

Example: generate the index HTML (and exit):

.. code-block:: none

    $ python hkshell.py 'g()'
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

    * *gen_indices* (fun(PostDB)) -- Function that generates indices.
    * *gen_posts* (fun(PostDB)) -- Function that generates the HTML files of
      the posts.
    * *edit_file* (fun(str) -> bool) -- Function that opens an editor with the
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

    * *config* (ConfigParser.ConfigParser) -- Configuration object.
    * *hkrc* (str) -- The name of the customization module.
      Default value: ``'hkrc'``.
    * *output* (object) -- When a hkshell function wants to print something, it
      calls *output*'s write method.
      Default value: sys.stdout
    * *callbacks* (Callbacks)
    """

    def __init__(self,
                 postdb=hkutils.NOT_SET,
                 config=hkutils.NOT_SET,
                 hkrc='hkrc',
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

    - *command* (``str``) -- The ``command`` attribute of the event that should
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
    set_feature('on', feature)

def off(feature):
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
    """Converts the argument to set(tag).
    
    Arguments:
    tags --
        Type: PreTagSet

    Returns: set(tag)

    Types:
        tag = str
        PreTagSet = tag | set(tag) | [tag]
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
    """Saves the post database and exits.

    If you want to exit without saving, just quit by hitting Ctrl-D.
    """

    event('before', 'x')
    postdb().save()
    event('after', 'x')
    sys.exit()

@hkshell_events()
def rl():
    """Reloads the post from the disk.

    Changes that have not been saved (e.g. with the :func:`x()` command) will
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

    - *ps* (``PrePostSet``)
    """
    for p in ps(pps):
        sum = p.subject() if len(p.subject()) < 40 \
            else p.subject()[:37] + '...'
        write('%s %s %s\n' % (p.author(), p.date(), sum))

def perform_operation(pps, command, operation):
    event('before', command)
    posts = ps(pps)
    event('postset_calculated', command, postset=posts)
    if len(posts) != 0:
        operation(posts)
    event('after', command, postset=posts)

def d(pps):
    """Deletes the posts in *pps*.
    
    **Argument:**

    - *pps* (PrePostSet)
    """

    perform_operation(pps, 'd', lambda posts: posts.forall.delete())

def dr(pps):
    """Deletes the posts in *pps* and all their children.

    **Argument:**

    - *pps* (PrePostSet)
    """

    perform_operation(pps, 'dr',
                      lambda posts: posts.expf().forall.delete())

@hkshell_events()
def j(pp1, pp2):
    """Joins two posts.

    Arguments:
    pp1 -- The post that will be the parent.
        Type: PrePost
    pp2 -- The post that will be the child.
        Type: PrePost
    """

    p1 = postdb().post(pp1)
    p2 = postdb().post(pp2)
    event('postset_calculated', 'j')
    if p1 != None and p2 != None:
        p2.set_parent(p1.heapid())

@hkshell_events()
def e(pp):
    """Edits a mail.

    Arguments:
    pp --
        Type: PrePost"""

    p = postdb().post(pp)
    if p != None:
        postdb().save()
        result = options.callbacks.edit_file(p.postfilename())
        if result == True:
            p.load()
    else:
        log('Post not found.')

@hkshell_events()
def dl(from_=0):
    email_downloader = hklib.EmailDownloader(postdb(), options.config)
    email_downloader.connect()
    email_downloader.download_new(int(from_))
    email_downloader.close()


##### Commands / tags #####

def pt(pps):
    """Propagates the tags of the given postset to all its children.
    
    Arguments:
    pps --
        Type: PrePostSet
    """

    def operation(posts):
        for post in posts:
            def add_tags(p):
                for tag in post.tags():
                    p.add_tag(tag)
            postdb().postset(post).expf().forall(add_tags)
    perform_operation(pps, 'pt', operation)

def at(pps, tags):
    """Adds the given tags to the given postset.
    
    Arguments:
    pps --
        Type: PrePostSet
    tags --
        Type: PreTagSet
    """

    tags = tagset(tags)
    def operation(posts):
        for p in posts:
            p.set_tags(tags.union(p.tags()))
    perform_operation(pps, 'at', operation)

def atr(pps, tags):
    """Adds the given tags to the posts of the given postset and all their
    consequences.

    Arguments:
    pps --
        Type: PrePostSet
    tags --
        Type: PreTagSet
    """

    tags = tagset(tags)
    def operation(posts):
        for p in posts.expf():
            p.set_tags(tags.union(p.tags()))
    perform_operation(pps, 'atr', operation)

def rt(pps, tags):
    """Removes the given tags to the given postset.
    
    Arguments:
    pps --
        Type: PrePostSet
    tags --
        Type: PreTagSet
    """

    tags = tagset(tags)
    def operation(posts):
        for p in posts:
            p.set_tags(set(p.tags()) - tags)
    perform_operation(pps, 'rt', operation)

def rtr(pps, tags):
    """Removes the given tags from the posts of the given postset and all their
    consequences.

    Arguments:
    pps --
        Type: PrePostSet
    tags --
        Type: PreTagSet
    """

    tags = tagset(tags)
    def operation(posts):
        for p in posts.expf():
            p.set_tags(set(p.tags()) - tags)
    perform_operation(pps, 'rtr', operation)

def st(pps, tags):
    """Sets the given tags on the given postset.
    
    Arguments:
    pps --
        Type: PrePostSet
    tags --
        Type: PreTagSet
    """

    tags = tagset(tags)
    def operation(posts):
        for p in posts:
            p.set_tags(tags)
    perform_operation(pps, 'st', operation)

def str_(pps, tags):
    """Removes the given tags from the posts of the given postset and all their
    consequences.

    Arguments:
    pps --
        Type: PrePostSet
    tags --
        Type: PreTagSet
    """

    tags = tagset(tags)
    def operation(posts):
        for p in posts.expf():
            p.set_tags(tags)
    perform_operation(pps, 'str_', operation)


##### Commands / subject #####

def pS(pps):
    """Propagates the subject of the given postset to all its children.
    
    Arguments:
    pps --
        Type: PrePostSet
    """

    def operation(posts):
        for post in posts:
            postdb().postset(post).expf().forall.set_subject(post.subject())
    perform_operation(pps, 'pS', operation)

def sS(pps, subject):
    """Sets the subject of given postset.
    
    Arguments:
    pps --
        Type: PrePostSet
    tags --
        Type: str
    """

    perform_operation(
        pps, 'sS', lambda posts: posts.forall.set_subject(subject))

def sSr(pps, subject):
    """Sets the subject of the posts of the given postset and all their
    consequences.

    Arguments:
    pps --
        Type: PrePostSet
    subject --
        Type: str
    """

    perform_operation(
        pps, 'sSr', lambda posts: posts.expf().forall.set_subject(subject))

def capitalize_subject(post):
    """Capitalizes the subject of the given post.

    Arguments:
    post --
        Type: Post
    """

    post.set_subject(post.subject().capitalize())

def cS(pps):
    """Capitalizes the subject of given postset.
    
    Arguments:
    pps --
        Type: PrePostSet
    """

    perform_operation(
        pps, 'cS', lambda posts: posts.forall(capitalize_subject))

def cSr(pps):
    """Capitalizes the posts of the given postset and all their consequences.

    Arguments:
    pps --
        Type: PrePostSet
    """

    perform_operation(
        pps, 'cSr', lambda posts: posts.expf().forall(capitalize_subject))


##### Main #####

def load_custom():
    """Loads the custom function when possible."""

    try:
        modname = options.hkrc
        module = __import__(modname)
        hklib.log('Customization module found (name: %s).' % (modname,))
    except ImportError:
        hklib.log('No customization module found.')
        return

    callbacks = options.callbacks
    for funname in ['gen_indices', 'gen_posts', 'edit_file']:
        try:
            setattr(callbacks, funname, getattr(module, funname))
            hklib.log(funname, ' custom function: loaded.')
        except AttributeError:
            hklib.log(funname, \
                          ' custom function: not found, using the default.')

def read_postdb():
    config = ConfigParser.ConfigParser()
    try:
        config.readfp(open('hk.cfg'))
    except IOError:
        print 'Heapkeeper config file "hk.cfg" does not exist!'
        sys.exit(1)
    return hklib.PostDB.from_config(config), config

def init():
    global modification_listener
    modification_listener = ModificationListener(postdb())
    listeners.append(modification_listener)

def main(args):
    options.postdb, options.config = read_postdb()
    load_custom()
    init()
    for arg in args:
        eval(arg)

if __name__ == '__main__':
    main(sys.argv[1:])

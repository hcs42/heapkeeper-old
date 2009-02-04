#!/usr/bin/python

"""heapia - Interactive heapmanipulator

For further help on a function type "help(<funname>)".

Functions:
h()                - prints this help
s()                - save
x()                - save and exit
g()                - generate index.html
ga()               - generate all html
gs()               - generate index.html and save
ps(pps)            - create a postset

pt(pps)            - propagate tags
at(pps, tag/tags)  - add tag/tags
atr(pps, tag/tags) - add tag/tags recursively
pS(pps)            - propagate subject
sS(pps, subj)      - set subject
sSr(pps, subj)     - set subject recursively
cS(pps, subj)      - capitalize the subject
cSr(pps, subj)     - capitalize the subject recursively
j(p, p)            - join two threads
set_auto_gen(bool) - setting autogeneration

Arguments will be evaluated as commands.
Example: generate the index HTML and exit:
    $ python heapia.py 'g()' 'exit()'

"""

import sys
import heapmanip

def h():
    print __doc__

def s():
    """Saves the mail database."""
    options['maildb'].save()

def x():
    options['maildb'].save()
    sys.exit()

options = {'auto_gen_var': True,
           'auto_save': True,
           'auto_threadstruct': True,
           'heapcustom': 'heapcustom',
           'callbacks': {'sections': lambda maildb: None}}

#    Some commands automatically re-generate the index.html when they run
#    successfully, if this option is True.

def get_option(option):
    """Returns the value of the given option.
    
    Arguments:
    option -- The name of the option.
        Type: str

    Returns: something
    """

    return options[option]

def set_option(option, value):
    """Sets the value of the given option.
    
    Arguments:
    option -- The name of the option.
        Type:
    value -- The new value of the option.
        Type: something
    """

    options[option] = value

def set_callback(callbackname, callbackfun):
    """Sets a callback function."""

    options['callbacks'][callbackname] = callbackfun

def auto():
    """(Re-)generates index.html if the auto option is true."""
    if options['auto_gen_var']:
        gen_index_html()
        sys.stdout.flush()
    if options['auto_save']:
        options['maildb'].save()
    if options['auto_threadstruct']:
        options['maildb'].threadstruct()

def gen_index_html():
    """Generates index.html."""
    sections = options['callbacks']['sections'](options['maildb'])
    g = heapmanip.Generator(options['maildb'])
    g.index_html(sections)

def gen_post_html():
    """Generates the html files for the posts."""
    g = heapmanip.Generator(options['maildb'])
    g.posts_to_html()

def g():
    gen_index_html()

def ga():
    gen_index_html()
    gen_post_html()

def gs():
    options['maildb'].save()
    gen_index_html()

def ps(pps):
    return options['maildb'].postset(pps)

def perform_operation(pps, operation):
    posts = ps(pps)
    if len(posts) == 0:
        log('Post not found.')
    else:
        operation(posts)
        auto()

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
        raise heapmanip.HeapException, \
              'Cannot convert object to tagset: %s' % (tags,)

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
            options['maildb'].postset(post).expf().forall(add_tags)
    perform_operation(pps, operation)

def at(pps, tags):
    """Adds the given tags to the given postset.
    
    Arguments:
    pps --
        Type: PrePostSet
    tags --
        Type: set(str) | [str]
    """

    tags = tagset(tags)
    def operation(posts):
        for p in posts:
            p.set_tags(tags.union(p.tags()))
    perform_operation(pps, operation)

def rt(pps, tags):
    """Removes the given tags to the given postset.
    
    Arguments:
    pps --
        Type: PrePostSet
    tags --
        Type: set(str) | [str]
    """

    tags = tagset(tags)
    def operation(posts):
        for p in posts:
            p.set_tags(tags.difference(p.tags()))
    perform_operation(pps, operation)

def atr(pps, tags):
    """Adds the given tags to the posts of the given postset and all their
    consequences.

    Arguments:
    pps --
        Type: PrePostSet
    tags --
        Type: set(str) | [str]
    """

    tags = tagset(tags)
    def operation(posts):
        for p in posts.expf():
            p.set_tags(tags.union(p.tags()))
    perform_operation(pps, operation)

def pS(pps):
    """Propagates the subject of the given postset to all its children.
    
    Arguments:
    pps --
        Type: PrePostSet
    """

    def operation(posts):
        for post in posts:
            options['maildb'].postset(post).expf().set_subject(post.subject())
    perform_operation(pps, operation)

def sS(pps, subject):
    """Sets the subject of given postset.
    
    Arguments:
    pps --
        Type: PrePostSet
    tags --
        Type: str
    """

    perform_operation(pps, lambda posts: posts.forall.set_subject(subject))

def sSr(pps, subject):
    """Sets the subject of the posts of the given postset and all their
    consequences.

    Arguments:
    pps --
        Type: PrePostSet
    subject --
        Type: str
    """

    perform_operation(pps, \
                      lambda posts: posts.expf().forall.set_subject(subject))

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

    perform_operation(pps, lambda posts: posts.forall(capitalize_subject))

def cSr(pps):
    """Capitalizes the posts of the given postset and all their consequences.

    Arguments:
    pps --
        Type: PrePostSet
    """

    perform_operation(pps,
                      lambda posts: posts.expf().forall(capitalize_subject))

def j(pp1, pp2):
    """Joins two mails.

    Arguments:
    pp1 -- The post that will be the parent.
        Type: PrePost
    pp2 -- The post that will be the child.
        Type: PrePost
    """

    p1 = options['maildb'].post(pp1)
    p2 = options['maildb'].post(pp2)
    if p1 != None and p2 != None:
        p2.set_inreplyto(p1.heapid())
        auto()
    else:
        log('Posts not found.')

def load_custom():
    """Loads the custom function when possible."""

    try:
        modname = options['heapcustom']
        module = __import__(modname)
        heapmanip.log('Customization module found (name: %s).' % (modname,))
    except ImportError:
        heapmanip.log('No customization module found.')
        return

    callbacks = options['callbacks']
    for funname in callbacks.keys():
        try:
            callbacks[funname] = getattr(module, funname)
            heapmanip.log(funname, ' custom function: loaded.')
        except AttributeError:
            heapmanip.log(funname, \
                          ' custom function: not found, using the default.')

def main(args):
    options['maildb'] = heapmanip.read_maildb()
    load_custom()
    for arg in args:
        eval(arg)

if __name__ == '__main__':
    main(sys.argv[1:])

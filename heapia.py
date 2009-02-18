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
d(pps)             - delete
dr(pps)            - delete recursively
j(pp, pp)          - join two threads
e(pp)              - edit the post as a file
dl()               - download new mail

maildb()           - the mail database object
set_option(option, value) - setting an option
get_option(option) - the value of an option

Argument types:
    pp = prepost = int | str | Post
    pps = prepostset = prepost | [prepost] | set(prepost) | PostSet

Options:
    maildb --- The mail database.
        Type: MailDB
    auto_gen_var --- If True, the index HTML will be regenerated after each
        command.
        Type: bool
    auto_save --- If True, the mail database will be saved after each command.
        Type: bool
    timing --- If True, the real (wall clock) time taken by commands is
        reported.
        Type: bool
    auto_threadstruct --- If True, the threadstruct will be regenerated after
        each command. It has only efficiency consequences, because later it
        will be regenerated later anyway.
        Type: bool
    heapcustom --- The module that is used to customize the behaviour of the
        commands.
        Type: str
    callbacks --- The callback functions. Don't change it manually, use the
        customization feature (heapcustom). If you want to modify it directly,
        use the set_callback function.

Callback functions (that can be defined in heapcustom.py):

    edit(file)
        Called when the user wants to edit a file (with the e() command). It
        should open some kind of text editor and return only when the editing
        is finished.

        Args:
            file --- The name of the mail file to be edited.

        Returns: whether the given file was modified and should be reread from
        the disk.

    gen_index_html(maildb):
        It should generate the index.html file.

        Args:
            maildb --- MailDB

        Returns: -

Arguments given to the script will be evaluated as commands.
Example: generate the index HTML (and exit):
    $ python heapia.py 'g()'
"""

import sys
import time
import subprocess
import heapmanip
import ConfigParser

start = time.time()

def h():
    print __doc__

def s():
    """Saves the mail database."""
    options['maildb'].save()

def x():
    options['maildb'].save()
    sys.exit()

def edit_default(file):
    subprocess.call(['gvim', '-f', file])
    return True

options = {'maildb': None,
           'config': None,
           'auto_gen_var': True,
           'auto_save': True,
           'timing': False,
           'auto_threadstruct': True,
           'heapcustom': 'heapcustom',
           'callbacks': {'sections': lambda maildb: None,
                         'gen_index_html': None,
                         'edit': edit_default}}

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

    if option not in options:
        raise heapmanip.HeapException, 'No such option: "%s"' % (option,)
    options[option] = value

def set_callback(callbackname, callbackfun):
    """Sets a callback function."""

    options['callbacks'][callbackname] = callbackfun

def maildb():
    return options['maildb']

def auto():
    """(Re-)generates index.html if the auto option is true."""
    if options['auto_gen_var']:
        gen_index_html()
        sys.stdout.flush()
    if options['auto_save']:
        maildb().save()
    if options['auto_threadstruct']:
        maildb().threadstruct()

def start_timing():
    global start
    start = time.time()

def end_timing():
    global start
    if options['timing']:
        print "%f seconds." % (time.time() - start)

def gen_index_html():
    """Generates index.html."""
    if options['callbacks']['gen_index_html'] != None:
        sections = options['callbacks']['gen_index_html'](maildb())
    else:
        sections = options['callbacks']['sections'](maildb())
        g = heapmanip.Generator(maildb())
        g.index_html(sections)

def gen_post_html():
    """Generates the html files for the posts."""
    g = heapmanip.Generator(maildb())
    g.posts_to_html()

def g():
    start_timing()
    gen_index_html()
    end_timing()

def ga():
    start_timing()
    gen_index_html()
    gen_post_html()
    end_timing()

def gs():
    start_timing()
    maildb().save()
    gen_index_html()
    end_timing()

def ps(pps):
    res = maildb().postset(pps)

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
            maildb().postset(post).expf().forall(add_tags)
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
            p.set_tags(set(p.tags()) - tags)
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
            maildb().postset(post).expf().forall.set_subject(post.subject())
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

def d(pps):
    """Deletes given postset.
    
    Arguments:
    pps --
        Type: PrePostSet
    """

    perform_operation(pps, lambda posts: posts.forall.delete())

def dr(pps):
    """Deletes the posts of the given postset and all their consequences.

    Arguments:
    pps --
        Type: PrePostSet
    """

    perform_operation(pps,
                      lambda posts: posts.expf().forall.delete())

def j(pp1, pp2):
    """Joins two mails.

    Arguments:
    pp1 -- The post that will be the parent.
        Type: PrePost
    pp2 -- The post that will be the child.
        Type: PrePost
    """

    p1 = maildb().post(pp1)
    p2 = maildb().post(pp2)
    if p1 != None and p2 != None:
        p2.set_inreplyto(p1.heapid())
        auto()
    else:
        log('Posts not found.')

def e(pp):
    """Edits a mail.

    Arguments:
    pp --
        Type: PrePost"""

    p = maildb().post(pp)
    if p != None:
        maildb().save()
        result = options['callbacks']['edit'](p.postfilename())
        if result == True:
            p.load()
            auto()
    else:
        log('Post not found.')

def dl(from_=0):
    server = heapmanip.Server(maildb(), options['config'])
    server.connect()
    server.download_new(int(from_))
    server.close()
    auto()

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

def read_maildb():
    config = ConfigParser.ConfigParser()
    config.read('heap.cfg')
    return heapmanip.MailDB.from_config(config), config

def main(args):
    options['maildb'], options['config'] = read_maildb()
    load_custom()
    for arg in args:
        eval(arg)

if __name__ == '__main__':
    main(sys.argv[1:])

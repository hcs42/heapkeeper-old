Tutorial
========

This page needs a major rewrite. It will contain a step-by-step example of the
followings:
* Creating a heap (with a Google Groups account and GMail account).
* Posting a few emails in order to create a non-trivial thread structure.
* Generating HTML from the heap.
* Modifying posts, thread structure and other things from the hkshell.

It should also have screenshots. (Most users will be lazy to do the tutorial
anyway, they just want to read it through in a few minutes in order to
understand how Heapkeeper works.)

Until then, here is the old content of the page:

Configuration
-------------

A config file has to be created in the current directory with the name
``heap.cfg``. An example config file::

    [server]
    host=imap.gmail.com
    port=993
    username=our.heap@gmail.com
    password=examplepassword

    [paths]
    mail=mail   # directory of the mail database
    html=html   # directory where the HTML should be generated

    [nicknames]
    1=Somebody somebody@gmail.com
    2=Somebody_else somebody.else@else.com

If the directory of the mail database does not exists, it will be created.
The html directory should contain heapindex.css; you can make for example a
symbolic link to the heapindex.css in the heap directory.

Using the interactive interface
-------------------------------

After creating the configuration file, the interactive interface can be started
by typing the following::

    $ ./heapia

This will start a Python shell and define the interactive commands as global
functions. You can type the h command (i.e. call the h function) to see the
available commands::

    >>> h()

If you type a command, the index.html will be automatically regenerated.
Most of the commands take a postset as their arguments. A postset can be
given in many ways:
* the heapid as a string (e.g. '42')
* the heapid as an integer (e.g. 42)
* the post as a Post object (e.g. maildb().post(42))
* a list or set of objects of any previous type (e.g. [42, '43'])
* a PostSet object (e.g. maildb().all())

E.g. the j command joins two posts (so the first given post will be the parent
of the second given post). To join posts with heapid 10 and 11::

    >>> j(10, 11)

Further examples::

    >>> e(12)           # Editing post 12. A GVim will open by default with the
                        # mail file that represents post 12. The following
                        # happens in the background: post 12 will be written to
                        # the disk, the editor will open; after the user closes
                        # the editor, the mail file will be read from the disk to
                        # the memory. So don't edit the mail file while the
                        # Heapkeeper is running, only with the e() command.

    >>> atr(20, 'git')  # Adding tag [git] to post 20 and all its descendants.

    >>> sS(ps([10,11,12]), 'something')  # Changing the subject of the given
                                         # posts to 'something'.

The heapmanip module can be used for more complicated tasks which does not have
an interface command. The following example collects the posts with [heap] tag
in the same threads as 11 and 14, and adds a 'Hey!\n' prefix to their bodies.
Then the mail HTML is regenerated. ::

    >>> heapmail = ps([11,14]).exp().collect.has_tag('heap')
    >>> heapmail.forall(lambda post: post.set_body('Hey!\n' + post.body()))
    >>> ga() # regenerate all HTML

Customizing the interface
-------------------------

heapia can be customized by creating a Python module called heapcustom. If the
appropriate callback functions are defined here, they will be used by heapia
instead of the default behaviour.

E.g. the following ``heapcustom.py`` changes the arguments of the
HTML-generator so that it includes the table of contents in the generated HTML
and omits the dates. ::

    import heapmanip

    def gen_index_html(maildb):
        g = heapmanip.Generator(maildb)
        g.index_html(write_toc=True, write_date=False)

The same can be done by hand from the Heapkeeper's interactive shell,
without creating ``heapcustom`` module::

    >>> def my_gen_index_html(maildb):
    ...     g = heapmanip.Generator(maildb)
    ...     g.index_html(write_toc=True, write_date=False)
    ...
    >>> set_callback('gen_index_html', my_gen_index_html)

If you want to use another editor (e.g. console Vim instead of GVim), put these
into the ``heapcustom.py``::

    import subprocess

    def edit_default(file):
        subprocess.call(['vim', file])
        return True

See module :mod:`heapcustom-csabahoch` as an example.

Using the interface without Python shell
----------------------------------------

The interface can be also used without interaction. Just call the heapia module
and give the commands as arguments. E.g. the following line typed into a Unix
shell will download the new mail and regenerate the HTML files::

    $ python heapia.py 'dl()' 'ga()'  # dl = download, ga = generate all HTML

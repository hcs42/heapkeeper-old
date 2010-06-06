Architecture of Heapkeeper
==========================

This section describes the architecture of Heapkeeper. First it gives a
high-level overview of the system by summarizing the role of each module in a
main directories and files in `Heapkeeper's repository`__:

__ http://github.com/hcs42/heapkeeper/

``README``, ``COPYING``
    Usual files about the program.
``doc/``
    Directory for documentation files. The ``rst`` files are text files with
    wiki-like syntax, and :ref:`Sphinx <development_sphinx>` can be used to
    generate HTML or other output from them.
``*.py``
    Python source files -- Heapkeeper itself.
``*.css``
    CSS files for the generated HTML files.

Module structure
----------------

Heapkeeper consists of several Python modules. Each module is implemented in
the file ``<module>.py``.

:mod:`hkutils`
    Contains general library classes and functions.
:mod:`hklib`
    The database and business logic of Heapkeeper. Its classes can
    download, store, and modify posts.
:mod:`hkgen`
    It generates HTML output from the posts on the heaps.
:mod:`hkshell`
    The interactive interface of Heapkeeper.
:mod:`hkbodyparser`
    It parses the body of the posts.
:mod:`hk`
    A small module whose only task is to invoke :mod:`hkshell`.
:mod:`hkcustomlib`
    Contains functions and classes that are useful for the parametrization of
    functions in other modules (especially functions of :mod:`hklib` and
    :mod:`hkshell`).
:mod:`issue_tracker`
    Generates HTML output that is like an issue tracker.
:mod:`hkrc_*`
    Initialization files of the developers. These module are not really part of
    Heapkeeper, but are kept in the Heapkeeper repository so that developers
    and users can learn from them, and developers can test if they break each
    other's hkrc.

The central modules are :mod:`hklib` and :mod:`hkshell`. The former contains
the core functionality of Heapkeeper, while the latter provides the primary
user interface. :mod:`hkgen` is also an important module, it generates HTML
pages from the post database. The general library functions that are not
related to the concepts of Heapkeeper are collected in :mod:`hkutils`.

Heapkeeper is a very customizable tool. :mod:`hkshell` can be customized
primarily by writing Python functions. The functions and classes of
:mod:`hkcustomlib` help to implement these custom functions. :mod:`hkgen` can
be customized by deriving own generator classes from the one in :mod:`hkgen`
and overriding some of its method. The :mod:`issue_tracker` is an example of
such a derived generator.

We use unit tests to test Heapkeeper's code, using the standard ``unittest``
module. Each module has a corresponding module that tests it.

:mod:`test_*`
    Modules that test another module.
:mod:`test`
    Module that tests all modules. Invokes the :mod:`test_*` modules.

Module contents
---------------

:mod:`hklib`: Classes that implement and manipulate the heap
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The main concept of Heapkeeper is the :ref:`heap <glossary_heap>`. The heap is
an abstract data structure that consists of :ref:`posts <glossary_post>`. The
heap data structure is implemented in the :mod:`hklib` module.

Heapkeeper stores the heaps (that consists of posts) on the disk. Each post is
stored in a :ref:`post file <glossary_post_file>`. When Heapkeeper runs, the
heaps on the disk are read and the heaps are stored in the memory as a
:class:`PostDB <hklib.PostDB>` object, which is called *post database*. Each
post is then stored in a :class:`Post <hklib.Post>` object, which we call *post
object* or just *post*. A post object can be re-written into its post file, and
re-read from its post file. A post is usually created from an email in the
first place, but later it may be modified in the heap.

:class:`hklib.Post`

    A :class:`Post <hklib.Post>` object (called a *post object*) represents
    a post.

    Each post has a unique id called :ref:`post id <glossary_post_id>` (e.g.
    ``usr/1``), which is the combination of a :ref:`heap id <glossary_heap_id>`
    (``'usr'``) and a :ref:`post index <glossary_post_index>` (``'1'``). The
    post file is in the directory that belongs to the heap (which is specified
    in the configuration file). The post file has the name ``<post
    index>.post``. The post object of a post stores its post id in a data
    attribute.

    A post consists of a *header* and a *body*. The header contains
    *attributes*, which are key-value pairs. Certain keys may have multiple
    values, but not all. The concepts of header, body and attribute and similar
    to these concepts wrt. emails.

    Both the header and the body is stored in the post object as data members.
    They are stored in the post file similarly to the standard email file
    format (:rfc:`2822`), but a little modification. The format is described in
    the documentation of :func:`hklib.Post.parse` (not yet).

    A post may have a *message id*, which is the ``Message-Id`` attribute in
    the header. The message id is the message id of the email from which the
    post was created. It is supposed to be unique.

    There are different relations between the posts: the most basic one is when
    a post is the child of another post. It usually means that the latter one
    is a reply to the former one. This information is stored in the ``Parent``
    attribute of the header of the child post: this attribute contains an id (a
    post id, a post index or message id) of the parent of the post. If there is
    no post found based on the id, or the id ``None``, the post does not have a
    parent. For more information about the relations, see
    :ref:`post_relations`. The ``Parent`` attribute of the post comes from the
    ``In-Reply-To`` attribute of the original email.

    A post may have :ref:`tags <glossary_tag>`, which tell us information
    about the topic of the post.

    A post may have *flags*, which tells Heapkeeper special information about
    the post. Currently there is only one flag, the ``deleted`` flag. When a
    post is deleted, it will not be removed entirely: the corresponding post
    object and post file will not be removed from the memory and the disk. The
    post will only obtain a ``deleted`` flag instead. It will keep its post id
    and message id; this way we achieve that no other post will have the same
    post id ever [#same_post_id]_. To save space and time, most attributes and
    the body of the post will be deleted, so the deletion cannot really be
    undone by Heapkeeper. Heapkeeper's database will handle deleted posts as if
    they would not exist, except that their post id is reserved.

    The body of a post is a string. We parse this string so that we can
    identify quotes (lines that start with ``>``), links and so-called *meta
    text* (text written between ``[`` and ``]``). Meta text is either meta
    information about the post for the readers or the maintainers of the heap
    (e.g. ``[todo The subject of this email should be corrected]``), or command
    that could be processed by Heapkeeper (e.g. ``[!delpost]``, which means
    that the current post should be deleted). The parsed string is called the
    *body object*.

:class:`hklib.PostDB`

    A :class:`PostDB <hklib.PostDB>` object (called a *post database*)
    represents the heap in the memory. It stores the post object of all
    posts. During initialization, it reads all the post files from the disk and
    creates the corresponding post objects. It can write the modified post
    files back at any time, or it can reload them from the disk.

    The post database calculates and stores the *thread structure*. The thread
    structure is a forest where the nodes are posts and the connections are
    :ref:`parent-child relations <post_relations>` between them. (Forest is a
    tree-like structure where having a root node it not necessary). The roots
    of the forest are the posts without parents. There may be posts that are
    excluded from the thread structure because they are in :ref:`cycles
    <cycle>`.

    The users of the post database can use the dictionary that describes the
    thread structure directly in order to get thread information. There are
    methods in :class:`PostDB <hklib.PostDB>`, however, that make obtaining
    most thread information easier. E.g. there are methods for calculating the
    root, the parent and the children of a post. There are also methods to find
    the cycles in the thread structure.

:class:`hklib.PostSet`

    See :ref:`here <glossary_post_set>`.

:class:`hklib.EmailDownloader`

    A :class:`EmailDownloader <hklib.EmailDownloader>` object can connect to an
    IMAP server, download new emails, create new posts based on the emails, and
    save them to the post database.

It may help to make a comparison between Heapkeeper and a program
that implements a relational database, e.g. MySQL:

+----------------------------------+-------------------------+
| Heapkeeper                       | MySQL                   |
+==================================+=========================+
| heap                             | relation database       |
+----------------------------------+-------------------------+
| :class:`PostDB <hklib.PostDB>`   | a data table            |
+----------------------------------+-------------------------+
| :class:`Post <hklib.Post>`       | a row in the data table |
+----------------------------------+-------------------------+
| Python                           | query language (SQL)    |
+----------------------------------+-------------------------+
| :class:`PostSet <hklib.PostSet>` | result of a query       |
+----------------------------------+-------------------------+

Module dependencies
-------------------

Understanding which module uses which other modules may help a lot in
understanding the system itself. We say that a module depends on another if it
uses functions or classes defined in the other module.

The module dependencies are shown in the following picture:

.. image:: images/module_deps.png

Since :mod:`hkutils` contains general library functions, it does not use any
other modules of Heapkeeper, but all the other modules may use it.
:mod:`hkshell`, :mod:`hkgen` and :mod:`hkcustomlib` all use :mod:`hklib`, since
:mod:`hklib` implements the data types that make the heap. :mod:`hkshell`
uses :mod:`hkcustomlib` only for setting sensible default values for certain
callback functions. :mod:`hkcustomlib` implements a callback function to
generate posts that invokes :mod:`hkgen`, but sometimes :mod:`hkshell` calls
into :mod:`hkgen` directly.

.. _testing:

Testing
-------

We use unit tests to test Heapkeeper's code, using the standard ``unittest``
module. Each module has a corresponding module that tests it. Our aim is to
reach almost 100% statement coverage. (Currently we have 74%, measured with
``coverage.py``.)

All tests can be executed using the :mod:`test` module:

.. code-block:: none

    $ python test.py

.. rubric:: Footnotes

.. [#same_post_id]
    Why is it important that post ids cannot be recycled? Imagine the following
    situation: the ``Parent`` field of post ``y`` contains the post id of
    ``x``, so ``x`` is the parent of ``y``. Then we delete ``x``; so ``y`` does
    not have a parent now. If a new post ``z`` would be created with the post
    id of ``x``, Heapkeeper would think it is the parent of ``y``, altough they
    may have nothing to do with each other.

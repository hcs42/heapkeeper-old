Glossary
========

.. include:: defs.hrst

.. _glossary_basic_concepts:

Basic concepts of Heapkeeper
----------------------------

.. _glossary_heap:

**Heap:**

    A heap is an editable mailing list. It is a changing set of :ref:`posts
    <glossary_post>`: new posts can be added, and existing posts can be
    modified. Usually there is a mailing list behind a heap which is piped into
    the heap, i.e. new emails will appear on the heap as new posts, where they
    can be modified (or even deleted). The heap is stored as a directory in the
    file system, in which each file is a :ref:`post file <glossary_post_file>`
    that stores a post. This directory is usually version controlled so that if
    some posts on the heap are modified, the modifications can be viewed later.
    Heapkeeper can manage several heaps simultaneously. Heaps are identified in
    Heapkeeper by their :ref:`heap id <glossary_heap_id>`.

.. _glossary_post:

**Post:**

    A post is a message that is stored on a :ref:`heap <glossary_heap>`. A post
    is uniquely identified by its :ref:`post id <glossary_post_id>`. Each post
    is stored in a :ref:`post file <glossary_post_file>`. A post has attributes
    (author, subject, tags, etc.) and a body. All of these are strings. When
    Heapkeeper is running, posts are represented as instances of the |Post|
    class.

.. _glossary_post_file:

**Post file:**

    A file in which a :ref:`post <glossary_post>` is stored. It has a very
    similar format to the email file format (:rfc:`2822`). An example of a
    post file::

        Author: ashe@usrobots.com
        Subject: RB-34

        RB-34 is behaving wierdly. You should have a look at it.
        I have never seen anything like that. It seems as if it
        could read my mind.

        Ashe

.. _glossary_post_id:

**Post id:**

    A post identifier that uniquely identifies a :ref:`post <glossary_post>`.
    It has two components: a :ref:`heap id <glossary_heap_id>` (which
    identifies the heap), and a :ref:`post index <glossary_post_index>` (which
    identities the post within the heap). For example ``usr/12`` is a post
    index, and it identities the post within the ``usr`` heap that has post
    index ``12``. Heapkeeper's shell accepts the post id either in a string
    format (``'usr/12'``) or in a tuple format (``('usr', '12')``).

.. _glossary_heap_id:

**Heap id:**

    A string that identifies a heap. The heap id will also be used as the name
    of the directory in which the HTML pages for the heap are generated, so it
    should not be an empty string and should not contain any character that
    is illegal in a file name.

.. _glossary_post_index:

**Post index:**

    A string that identifies a post within a heap. Usually (but not
    necessarily) post indices are integers. In Heapkeeper's shell, post indices
    that are indeed integers may also be specified as integers (e.g. ``12``),
    not only as strings (e.g. ``'12'``).

.. _glossary_post_set:

**Post set:**

    A set of posts on which operations can be performed. A set of posts is
    represented by an instance of the |PostSet| class.

.. _post_relations:

Relation between the posts
--------------------------

*Primitive* means that a concept cannot be defined using other concepts
mentioned here, because they are stored by the post. All primitive concepts are
explicitly noted to be primitive. Actually, there are only two primitives:
*parent* and *reference*.

.. _glossary_parent_child:

**Parent (primitive), child:**

    Post X and Y can be in a parent-child relation. A post may have
    only one or zero parents, but any number of children. Threads
    are based on parent-child relationships.

    The ``Parent`` header of the post object of Y refers to X (e.g. by its post
    id or message id) iff X is parent of Y. When an email is downloaded, it's
    ``In-Reply-To`` header will be automatically converted to a ``Parent``
    header of the post object, i.e. a parent-reference.

    See also:

    * :func:`hklib.Post.parent`
    * :func:`hklib.PostDB.parent`
    * :func:`hklib.PostDB.children`

.. _glossary_root:

**Root:**

    Every post has a root, which is another post. If a post has no
    parent, it is its own root. Otherwise, the root of the parent is
    the root of the post. We also say that a post is a root if it has
    no parent. So the word 'root' is used both as a relation (X is the
    root of Y) and a plain noun (X is a root).

    See also:

    * :func:`hklib.PostDB.root`

.. _glossary_reference:

**Reference (primitive):**

    A post may refer to any number of other posts. Sometimes if Y is
    a reply to X, the maintainer of the heap decides that X should be
    only a reference in Y instead of being the parent of Y.

    The references of a post are stored in the post object.

.. _glossary_ancestor:

**Ancestor:**

    If a post has no parent, it has no ancestors. Otherwise the
    ancestors of a post are its parent and the ancestors of its
    parent.

    More informally: the ancestors of a post are its parent, its
    parent's parent, etc.

    See also:

    * :func:`hklib.PostSet.expb`

.. _glossary_descendant:

**Descendant:**

    If a post has no children, it has no descendants. Otherwise the
    ancestors of a post are its children and the descendants of its
    children.

    More informally: the descendant of a post are its children, its
    children's children, etc.

    See also:

    * :func:`hklib.PostSet.expf`

.. _glossary_thread:

**Thread:**

     A thread is the set of a root and all its descendants. A thread
     contains exactly one post that has no parent, which is the root of
     the thread. (The third meaning of 'root' :) ) Obviously, the root
     of the thread is a root; and it is the root of all posts in the
     thread. (And it is not a root of any other post.)

.. _glossary_subthread:

**Subthread:**

     A subthread is the set of a post and its descendants. That post
     is called the root of the subthread (although it does not have
     to be root in the sense that it may have a parent). A subthread
     may or may not be a thread. A subthread is a thread if and only
     if its root (i.e. the post which together with its descendants
     makes up the subset) is a root (i.e. it has no parent). The root
     of all posts in the subthread is the same. If the subthread is
     not a thread, this root differs from the root of the subthread,
     and it is also the root of other posts outside the subthread.

.. _cycle:
.. _glossary_cycle:

**Cycle:**

    Each post is in exactly one thread; except for the posts that are
    in a cycle. Those posts are not present in any thread. A post is
    in a cycle if you can go up via the *parent* relation infinitely
    long and you will never reach a root. The cycles are handled by
    Heapkeeper, but the maintainer of the heap should remove the cycles.

    See also:

    * :func:`hklib.PostDB.has_cycle`
    * :func:`hklib.PostDB.cycles`

.. _glossary_thread_mate:

**Thread mate:**

    Two threads are thread mates if they have the same root, i.e. they
    are in the same thread. (Posts in cycles do not have thread
    mates.)

    See also:

    * :func:`hklib.PostSet.exp`

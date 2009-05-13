Glossary
========

.. _post_relations:

Relation between the posts
--------------------------

*Primitive* means that it cannot be defined using other concepts mentioned
here, because they are stored by the post. All primitive concepts are
explicitly noted to be primitive. Actually, there are only two primitives:
*parent* and *reference*.

**Parent (primitive), child:**
    Post X and Y can be in a parent-child relation. A post may have
    only one or zero parents, but any number of children. Threads
    are based on parent-child relationships.
  
    The in-reply-to header of the post object of Y refers to X
    (either by its heapid or messid) iff X is parent of Y. When a
    post is downloaded, it's in-reply-to header will be
    automatically converted to an in-reply-to header of the
    post object, i.e. a parent-reference.
  
    The code uses 'inreplyto' in many places, but I suggest
    replacing those by 'parent'.
  
    See also:
    
    * :func:`hklib.Post.parent`
    * :func:`hklib.PostDB.parent`
    * :func:`hklib.PostDB.children`

**Root:**
    Every post has a root, which is another post. If a post has no
    parent, it is its own root. Otherwise, the root of the parent is
    the root of the post. We also say that a post is a root if it has
    no parent. So the word 'root' is used both as a relation (X is the
    root of Y) and a plain noun (X is a root).

    See also:
    
    * :func:`hklib.PostDB.root`

**Reference (primitive):**
    A post may refer to any number of other posts. Sometimes if Y is
    a reply to X, the maintainer of the heap decides that X should be
    only a reference in Y instead of being the parent of Y.

    The references of a post are stored in the post object.

**Ancestor:**
    If a post has no parent, it has no ancestors. Otherwise the
    ancestors of a post are its parent and the ancestors of its
    parent.

    More informally: the ancestors of a post are its parent, its
    parent's parent, etc.

    See also:
    
    * :func:`hklib.PostSet.expb`

**Descendant:**
    If a post has no children, it has no descendants. Otherwise the
    ancestors of a post are its children and the descendants of its
    children.

    More informally: the descendant of a post are its children, its
    children's children, etc.

    See also:
    
    * :func:`hklib.PostSet.expf`

**Thread:**
     A thread is the set of a root and all its descendants. A thread
     contains exactly one post that has no parent, which is the root of
     the thread. (The third meaning of 'root' :) ) Obviously, the root
     of the thread is a root; and it is the root of all posts in the
     thread. (And it is not a root of any other post.)

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

**Cycle:**
    Each post is in exactly one thread; except for the posts that are
    in a cycle. Those posts are not present in any thread. A post is
    in a cycle if you can go up via the *parent* relation infinitely
    long and you will never reach a root. The cycles are handled by
    Heapkeeper, but the maintainer of the heap should remove the cycles.

    See also:
    
    * :func:`hklib.PostDB.has_cycle`
    * :func:`hklib.PostDB.cycles`

**Thread mate:**
    Two threads are thread mates if they have the same root, i.e. they
    are in the same thread. (Posts in cycles do not have thread
    mates.)

    See also:
    
    * :func:`hklib.PostSet.exp`

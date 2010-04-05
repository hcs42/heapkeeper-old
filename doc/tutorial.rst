Tutorial
========

.. include:: defs.hrst

This tutorial describes how to use Heapkeeper. It will show:

- how to download__ and configure__ Heapkeeper
- how to add__ posts to a local heap
- how to generate__ HTML pages from them
- how to manipulate__ the posts in the heap
- how to create a heap for a `mailing list`__

__ downloading_hk_
__ configuring_hk_
__ adding_posts_
__ generating_html_
__ manipulating_posts_
__ mailing_list_

Table of contents
-----------------

- `Downloading Heapkeeper`__
- `Configuration`__
- `Adding a new post to the heap`__
- `Adding new posts to the heap from outside hkshell`__
- `Generating HTML pages`__
- `Modifying the heap with hkshell`__
- `Creating a heap for a mailing list`__

__ downloading_hk_
__ configuring_hk_
__ adding_posts_
__ adding_posts_from_outside
__ generating_html_
__ manipulating_posts_
__ mailing_list_

.. _downloading_hk:

Downloading Heapkeeper
----------------------

First make sure you have Python 2.5 or 2.6.

Then download the latest version of Heapkeeper (either in `tar.gz`__ or in
`zip`__). For Unix users:

.. code-block:: sh

    $ wget http://heapkeeper.org/releases/heapkeeper-0.5.tar.gz

__ http://heapkeeper.org/releases/heapkeeper-0.5.tar.gz
__ http://heapkeeper.org/releases/heapkeeper-0.5.zip

Unzip the tar.gz or zip file. For Unix users:

.. code-block:: sh

    $ tar xzf heapkeeper-0.5.tar.gz

Make Heapkeeper's directory the current one. Heapkeeper's shell (|hkshell|) can
be started from here without any installation procedure. You can ask for
version information for example:

.. code-block:: sh

    $ cd heapkeeper-0.5
    $ python hk.py --version
    Heapkeeper version 0.5

Or you can execute the automatic test:

.. code-block:: sh

    $ python test.py
    ----------------------------------------------------------------------
    Ran 126 tests in 0.172s

    OK

.. _configuring_hk:

Configuration
-------------

First, we create two directories: ``posts`` and ``html``. ``posts`` will store
the :ref:`heap <glossary_heap>`, i.e. the post database, which contains the
:ref:`posts <glossary_post>` themselves in text files (so-called :ref:`post
files <glossary_post_file>`). The ``html`` directory will contain the HTML
pages that will be generated from the posts.

.. code-block:: sh

    $ mkdir posts
    $ mkdir html

Heapkeeper needs a file called ``hk.cfg`` in which its settings are stored.
We set the directories that we just created to be used as post database and
HTML generation target.

.. code-block:: ini

    [paths]
    html_dir=html

    # Heap for U.S. Robots and Mechanical Men, Inc.
    [heaps/usr]
    path=posts

.. _adding_posts:

Adding a new post to the heap
-----------------------------

Normally, the :ref:`posts <glossary_post>` on the heap are emails that were
downloaded from IMAP servers and converted into a post. To make it easier to
understand this tutorial, first we will create and manipulate posts locally by
|hkshell| commands. (Afterwards we will go through on how to download emails
from a mailing list, which makes Heapkeeper actually usable.)

Start |hkshell|:

.. code-block:: sh

    $ python hk.py
    Importing hkrc...
    Module not found: "hkrc"

    >>>

The output informs us that |hkshell| did not find the customization module
(``hkrc``), but that is all right. The last line indicates that we got a Python
prompt where we can type any Python statement. Actually, |hkshell| commands are
Python functions imported into the global namespace.

Let's list all the posts we have (of course we don't have any posts yet)::

    >>> postdb().all()
    PostSet([])

Let's create now a new post with the |enew| command in the ``'usr'`` heap::

    >>> enew(heap_id='usr')

An editor will pop up that lets you edit the post to be created. By default,
the editor is ``notepad`` on Windows and ``vi`` on Unix systems; this can be
overridden by setting the ``EDITOR`` environment variable. If you realize that
its not your favourite editor that was opened, just exit without doing
anything. In this case no post will be created.

The editor will contain the following template:

.. code-block:: none

    Author:
    Subject:

Paste this in place of the template:

.. code-block:: none

    Author: ashe@usrobots.com
    Subject: RB-34
    Tag: interesting
    Tag: robot

    RB-34 is behaving wierdly. You should have a look at it.
    I have never seen anything like that. It seems as if it
    could read my mind.

    Ashe

The post specifies the author and the subject, which are the same concepts as
in emails. Posts may also have any number of tags; this post has two tags. The
header is closed with an empty line, which is followed by the body of the post.
This structure is similar to the standard email file format (:rfc:`2822`).

After saving and quitting from the text editor, we should see confirmation
about the post's successful creation::

    >>> enew(heap_id='usr')
    Post created.
    <post '1'>

At this point, the post exists only in the memory. We use the :func:`s
<hkshell.s>` command to save everything to the disk::

    >>> s()

A file called ``1.post`` has been created in the ``posts`` directory. It
contains exactly what we pasted into the text editor. Let's quit from
Heapkeeper with the |x| command and examine ``posts/1.post``:

.. code-block:: none

    >>> x()
    $ ls posts/
    1.post
    $ cat posts/1.post
    Author: ashe@usrobots.com
    Subject: RB-34
    Tag: interesting
    Tag: robot

    RB-34 is behaving wierdly. You should have a look at it.
    I have never seen anything like that. It seems as if it
    could read my mind.

    Ashe

.. _adding_posts_from_outside:

Adding new posts to the heap from outside hkshell
-------------------------------------------------

The post database on the disk (i.e. the post directory) can be manipulated by
hand. (Heapkeeper is not running now, so we will not interfere with it.) Let's
create a few more posts to make the thread structure more interesting. The
``Parent`` attribute is used to specify the parent of a post -- to which the
current post is a reply.

The following Unix shell commands can be copy-pasted into the terminal or a
shell script file. They will create the posts we will work with. (If you don't
have a Unix shell, you can create the post files in the same way we created
``1.post``).

.. code-block:: sh

    cat >posts/2.post <<EOF
    Author: alfred.lanning@usrobots.com
    Parent: 1
    Subject: Re: RB-34
    Tag: robot
    Tag: interesting

    The robot is strange, indeed, probably some error
    happened during the manufacturing process. Susan should
    have it tested psychologically. Peter, could you express
    the problem mathematically?

    Alfred
    EOF

    cat >posts/3.post <<EOF
    Author: peter.bogert@usrobots.com
    Parent: 2
    Subject: Re: RB-34
    Tag: robot
    Tag: interesting

    Yes, sure.

    Peter
    EOF

    cat >posts/4.post <<EOF
    Author: susan@usrobots.com
    Parent: 2
    Subject: Re: RB-34
    Tag: robot
    Tag: interesting
    Tag: psychology

    I have talked to the robot. It likes reading only novels
    and other literature, it is not interested in natural
    sciences. It is very bright, though.

    Susan
    EOF

    cat >posts/5.post <<EOF
    Author: alfred.lanning@usrobots.com
    Parent: 3
    Subject: Re: RB-34
    Tag: robot
    Tag: interesting

    Peter, have you made any progress?

    Alfred
    EOF

    cat >posts/6.post <<EOF
    Author: alfred.lanning@usrobots.com
    Parent: 4
    Subject: Re: RB-34
    Tag: robot
    Tag: interesting
    Tag: psychology

    Susan, what do you mean by bright?

    Alfred
    EOF

    cat >posts/7.post <<EOF
    Author: susan@usrobots.com
    Parent: 6
    Subject: Re: RB-34
    Tag: robot
    Tag: interesting
    Tag: psychology

    I mean it is understands natural sciences very well, it
    just does not care.

    Susan
    EOF

    cat >posts/8.post <<EOF
    Author: susan@usrobots.com
    Subject: Cinema
    Tag: free time

    Other subject. Does anyone feel like going to the cinema?

    Susan
    EOF

.. _generating_html:

Generating HTML pages
---------------------

The posts and the threads can be visualized in HTML using the |g| command (it
stands for "generate")::

    $ python hk.py
    Importing hkrc...
    Module not found: "hkrc"

    >>> g()
    Generating index.html...
    Generating thread pages...

Open ``html/index/index.html`` in a browser. You will see something like this:

.. image:: images/1.png
      :align: center

This is called an *index page*, because it contains an index of the posts. Every
post has a one line summary. These post summaries are sorted into boxes: every
box is a thread. Now there are only two threads, the second of which contains
only one post. In the first box, the posts are ordered in a threaded structure:
for example both post 3 and 4 are replies to post 2.

A post summary shows the author, the subject, the tags and the id (so-called
*heapid*) of the post. The heapids are links, so we can click on them to read
the posts. If we click on the heapid of the second post, the following page
will be shown to us:

.. image:: images/2.png
      :align: center

This page contains the thread in which post 2 is located. The parent of each
post is written after its heapid after an arrow sign.

.. _manipulating_posts:

Modifying the heap with |hkshell|
---------------------------------

The collection of the posts is called the *heap*. One of Heapkeeper's aims is to
make it easy to perform operations of large amount of posts. Theoretically, you
can do anything you want with the post database that is stored in the post
files: you can use text editors, Unix text processing tools to modify the heap,
or even write own scripts and programs.

A more convenient way to do this is to use Heapkeeper's shell and API. We
already used the former one to create a new post and to generate the HTML pages.
Now we will use it to perform more complicated operations.

|hkshell| commands
""""""""""""""""""

The most common operations can be performed quite easily using the appropriate
|hkshell| command. (We already used the |enew|, |s|, |x| and |g| commands.)
These commands are very high-level. Not everything can be done with them, they
are only handy shortcuts. They are to be used often, so they all have fairly
short names that are essentially mnemonics. See the list of |hkshell| commands
:ref:`here <hkshell_commands>`.

|ls| and |cat|
::::::::::::::

First let's have a look at the |ls| command. It prints out the header of given
post or posts, which can be specified for example by their heapid. If no posts
are specified, it prints the header of all posts. The posts in the output of
|ls| have the same indentation as in the index page that we saw previously. ::

    >>> ls('usr/1')
    <usr/1> RB-34  ashe@usrobots.com
    >>> ls(['usr/1', 'usr/2'])
    <usr/1> RB-34  ashe@usrobots.com
      <usr/2> RB-34  alfred.lanning@usrobots.com
    >>> ls()
    <usr/1> RB-34  ashe@usrobots.com
      <usr/2> RB-34  alfred.lanning@usrobots.com
        <usr/3> RB-34  peter.bogert@usrobots.com
          <usr/5> RB-34  alfred.lanning@usrobots.com
        <usr/4> RB-34  susan@usrobots.com
          <usr/6> RB-34  alfred.lanning@usrobots.com
            <usr/7> RB-34  susan@usrobots.com
    <usr/8> Cinema  susan@usrobots.com
    >>>

The |cat| command prints the post itself::

    >>> cat('usr/1')
    Post-id: usr/1
    Author: ashe@usrobots.com
    Subject: RB-34
    Tag: interesting
    Tag: robot

    RB-34 is behaving wierdly. You should have a look at it.
    I have never seen anything like that. It seems as if it
    could read my mind.

    Ashe

Heap hint, |sh| and |gh|
::::::::::::::::::::::::

Previously we referred to a post with its :ref:`post id <glossary_post_id>`
(e.g. ``usr/1``), which is the combination of its :ref:`heap id
<glossary_heap_id>` (``'usr'``) and its post index (``'1'``). If we specify a
"heap hint", then we can use only the post index, and Heapkeeper will try to
find the post it within that heap.

Let's set the heap hint to ``'usr'``::

    >> sh('usr')

Now can just refer to post 1 (``1`` can be given either as a string or as an
integer)::

    >>> ls(1)
    <usr/1> RB-34  ashe@usrobots.com

The heap hint can be printed using |gh|::

    >>> gh()
    'usr

Manipulating the subject and tags
:::::::::::::::::::::::::::::::::

Now let's have a look at the commands that actually modify the posts. For
example the |sS| command ("set subject") sets the subject of the given posts.
An example::

    >>> sS([1, 2], 'Robot Problem: RB-34')
    >>> ls()
    <usr/1> Robot Problem: RB-34  ashe@usrobots.com
      <usr/2> Robot Problem: RB-34  alfred.lanning@usrobots.com
        <usr/3> RB-34  peter.bogert@usrobots.com
          <usr/5> RB-34  alfred.lanning@usrobots.com
        <usr/4> RB-34  susan@usrobots.com
          <usr/6> RB-34  alfred.lanning@usrobots.com
            <usr/7> RB-34  susan@usrobots.com
    <usr/8> Cinema  susan@usrobots.com

There is a recursive version of |sS| that is called |sSr| ("set subject
recursively"). It changes not only the subject of the given post, but the
subject of all its descendants. For example, to change the subject of all
emails in the "Robot" thread, we can set the subject of the root post
recursively, and all posts' subject will be set::

    >>> sSr(1, 'Mind-reader robot')
    >>> ls()
    <usr/1> Mind-reader robot  ashe@usrobots.com
      <usr/2> Mind-reader robot  alfred.lanning@usrobots.com
        <usr/3> Mind-reader robot  peter.bogert@usrobots.com
          <usr/5> Mind-reader robot  alfred.lanning@usrobots.com
        <usr/4> Mind-reader robot  susan@usrobots.com
          <usr/6> Mind-reader robot  alfred.lanning@usrobots.com
            <usr/7> Mind-reader robot  susan@usrobots.com
    <usr/8> Cinema  susan@usrobots.com


There are similar functions to control tags, for example |aT| ("add tag"),
|aTr| ("add tag recursively"), |rT| ("remove tag") and |rTr| ("remove tag
recursively").

The |j| command: joining posts
::::::::::::::::::::::::::::::

The thread structure can also be changed: the |j| command joins two posts. It
means that the second post will be a child of the first post. It does not
matter whether it had another parent before or it had no parent.

Let's write an answer to the "Cinema" post, but let's forget to mention that it
should be the child of that post! (This happens often in real life with email
clients, especially when people modify the subject of the email they are
answering to.) Let's use the |enew_str| function to create the new post. It
works like |enew|, but receives the content of the post as an argument::

    >>> enew_str("Author: ashe@usrobots.com\n"
    ...          "Subject: Cinema\n"
    ...          "\n"
    ...          "Yes, I'd like to go!\n"
    ...          "\n"
    ...          "Ashe\n")
    Post created.
    <post usr/9>
    >>> g()
    Generating index.html...
    Generating thread pages...

The generated page will look like this:

.. image:: images/4.png
      :align: center

Let's join post 8 and 9 and regenerate the index page::

    >>> j(8, 9)
    >>> g()
    Generating index.html...
    Generating thread pages...

On the new index page, we will see that the two "Cinema" posts are in one
thread now, and post 8 is the parent of post 9:

.. image:: images/5.png
      :align: center

Posts
"""""

The most basic data structure of Heapkeeper is :class:`hklib.Post`. A |Post|
object represents a post, and it stores the attributes and the body of the post
that it represents. The simplest way to obtain the |Post| object of a post in
|hkshell| is using its :ref:`post id <glossary_post_id>` and the |p| function::

    >>> post = p(1)
    >>> print post
    <post usr/1>

(We don't have to specify the heap because we set the heap hint to ``'usr'``
before using the |sh| command.)

The |Post| class has functions for getting and setting the attributes and the
body. The getter functions work in a quite obvious way::

    >>> post = p(1)
    >>> print post
    <post usr/1>
    >>> post.post_id()
    ('usr', '1')
    >>> post.post_id_str()
    'usr/1'
    >>> post.heap_id()
    'usr'
    >>> post.post_index()
    '1'
    >>> post.author()
    'ashe@usrobots.com'
    >>> post.subject()
    'Mind-reader robot'
    >>> post.tags()
    ['interesting', 'robot']
    >>> post.body()
    'RB-34 is behaving wierdly. You should have a look at it
    .\nI have never seen anything like that. It seems as if
    it\ncould read my mind.\n\nAshe\n'

Let's create a new post and change its content using |Post| methods! ::

    >>> post = enew_str('Author: someone')
    Post created.
    >>> post.author()
    'someone'
    >>> post.subject()
    ''
    >>> post.body()
    '\n'
    >>> post.set_author('noname spammer')
    >>> post.set_subject('Ugly spam')
    >>> post.set_body('Buy r0b0t for $99!\n'
    ...               '\n'
    ...               'http://buyrobot99.com')
    >>> cat(post)
    Post-id: usr/10
    Author: noname spammer
    Subject: Ugly spam

    Buy r0b0t for $99!

    http://buyrobot99.com

A post can be deleted either using the :class:`Post.delete <hklib.Post.delete>`
method or the |d| command. After deletion, the heapid will remain occupied and
the |Post| object will still exist, but the post will not show up in either the
generated HTML pages, or in the result of :func:`postdb().all()
<hklib.PostDB.all>` or :func:`ls() <hkshell.ls>`. Its content will be replaced
by a placeholder content::

    >>> ls()
    <usr/1> Mind-reader robot  ashe@usrobots.com
      <usr/2> Mind-reader robot  alfred.lanning@usrobots.com
        <usr/3> Mind-reader robot  peter.bogert@usrobots.com
          <usr/5> Mind-reader robot  alfred.lanning@usrobots.com
        <usr/4> Mind-reader robot  susan@usrobots.com
          <usr/6> Mind-reader robot  alfred.lanning@usrobots.com
            <usr/7> Mind-reader robot  susan@usrobots.com
    <usr/10> Ugly spam  noname spammer
    <usr/8> Cinema  susan@usrobots.com
      <usr/9> Cinema  ashe@usrobots.com
    >>> d(10)
    >>> ls()
    <usr/1> Mind-reader robot  ashe@usrobots.com
      <usr/2> Mind-reader robot  alfred.lanning@usrobots.com
        <usr/3> Mind-reader robot  peter.bogert@usrobots.com
          <usr/5> Mind-reader robot  alfred.lanning@usrobots.com
        <usr/4> Mind-reader robot  susan@usrobots.com
          <usr/6> Mind-reader robot  alfred.lanning@usrobots.com
            <usr/7> Mind-reader robot  susan@usrobots.com
    <usr/8> Cinema  susan@usrobots.com
      <usr/9> Cinema  ashe@usrobots.com
    >>> cat(10)
    Post-id: usr/10
    Flag: deleted

Post sets
"""""""""

Most |hkshell| commands take a :ref:`post set <glossary_post_set>` as an
argument. They accept :class:`hklib.PostSet` objects, as well as a few other
types that can be converted to |PostSet|. We saw examples of the followings,
all of which can be converted to |PostSet| objects:

* the :ref:`post index <glossary_post_index>` as an integer (e.g. ``sS(42,
  'something')``)
* the post index as a string (e.g. ``sS('43', 'something')``)
* the :ref:`post id <glossary_post_id>` as a string (e.g. ``sS('usr/43',
  'something')``)
* a list or set of any of the previous types (e.g. ``sS([42, '43', 'usr/44'],
  'something')``)

The |PostSet| object can also be created explicitly, using the |ps| function::

    >>> posts = ps([8, 9])
    >>> print posts
    PostSet([<post usr/8>, <post usr/9>])
    >>> sS(posts,'How about cinema?')
    >>> ls(posts)
    <usr/8> How about cinema?  susan@usrobots.com
      <usr/9> How about cinema?  ashe@usrobots.com

:func:`postdb().all() <hklib.PostDB.all>` returns a post set that contains all
posts. In the following example, we use it to add the ``internal`` tag to all
posts::

    >>> aT(postdb().all(), 'internal')
    >>> ls(show_tags=True, show_author=False)
    <usr/1> Mind-reader robot  [interesting,internal,robot]
      <usr/2> Mind-reader robot  [interesting,internal,robot]
        <usr/3> Mind-reader robot  [interesting,internal,robot]
          <usr/5> Mind-reader robot  [interesting,internal,robot]
        <usr/4> Mind-reader robot  [interesting,internal,psychology,robot]
          <usr/6> Mind-reader robot  [interesting,internal,psychology,robot]
            <usr/7> Mind-reader robot  [interesting,internal,psychology,robot]
    <usr/8> How about cinema?  [free time,internal]
      <usr/9> How about cinema?  [internal]

There are many things we can do with a post set. It has standard set operations
like union, intersection, etc; but it also has operations that are specific to
Heapkeeper. For example :func:`p.expf() <hklib.PostSet.expf>` ("expand
forward") returns a post set that contains all posts of `p` and all their
descendants. If we expand post 1, we will get all posts concerning the
mind-reader robot::

    >>> ls(ps([1]).expf())
    <usr/1> Mind-reader robot  ashe@usrobots.com
      <usr/2> Mind-reader robot  alfred.lanning@usrobots.com
        <usr/3> Mind-reader robot  peter.bogert@usrobots.com
          <usr/5> Mind-reader robot  alfred.lanning@usrobots.com
        <usr/4> Mind-reader robot  susan@usrobots.com
          <usr/6> Mind-reader robot  alfred.lanning@usrobots.com
            <usr/7> Mind-reader robot  susan@usrobots.com


|PostSet| has two special attributes: |collect| and |forall|.
|collect| collects posts from a post set which have certain property.
|forall| applies a function to all posts in a post set. For example, let's say
we want to rename the tag ``psychology`` to ``psycho``. First we collect the
posts that have the ``psychology`` tag, then remove these tags (using |rT|) and
add ``psycho`` instead (using |aT|)::

    >>> posts = postdb().all().collect(lambda p: p.has_tag('psychology'))
    >>> posts
    PostSet([<post usr/4>, <post usr/6>, <post usr/7>])
    >>> posts.forall(lambda p: rT(p, 'psychology'))
    >>> posts.forall(lambda p: aT(p, 'psycho'))
    >>> ls(show_tags=True, show_author=False)
    <usr/1> Mind-reader robot  [interesting,internal,robot]
      <usr/2> Mind-reader robot  [interesting,internal,robot]
        <usr/3> Mind-reader robot  [interesting,internal,robot]
          <usr/5> Mind-reader robot  [interesting,internal,robot]
        <usr/4> Mind-reader robot  [interesting,internal,psycho,robot]
          <usr/6> Mind-reader robot  [interesting,internal,psycho,robot]
            <usr/7> Mind-reader robot  [interesting,internal,psycho,robot]
    <usr/8> How about cinema?  [free time,internal]
      <usr/9> How about cinema?  [internal]

.. _mailing_list:

Creating a heap for a mailing list
----------------------------------

As you probably understand now, Heapkeeper is for managing heaps, which are
modifiable mailing list archives. So far we added new posts to the heap with
|hkshell| commands.

One of Heapkeeper's major features is to convert emails arriving to a real
mailing list automatically to posts on a heap. Currently this can be done using
an email account, which will serve as a channel between the mailing list and
Heapkeeper. The reason for this is the following. Heapkeeper can download the
emails of the mailing list via IMAP protocol with SSL. Since mailing lists do
not support IMAP, but email accounts usually do, Heapkeeper will need an email
account (with IMAP SSL) as a channel, through which it can download emails.

In this section of the tutorial, we will create an email account and use
Heapkeeper to download emails from there. The last step (which we will not
perform here) would be to create a mailing list (e.g. GoogleGroups) and
subscribe with the email account. The account will then be used as a channel,
so that Heapkeeper would download emails arriving to the mailing list.

Let's create a GMail account first. It can be done at
http://mail.google.com/mail/signup. In the example, we used the
``myheap.channel`` user name.

Then modify the configuration file so that Heapkeeper will know where to
download the emails from:

.. code-block:: none

    [paths]
    html_dir=html

    [heaps/myheap]
    path=myheap_posts

    [heaps/myheap/server]
    host=imap.gmail.com
    port=993
    username=myheap.channel@gmail.com

Start Heapkeeper:

.. code-block:: sh

    $ ./hk.py
    Warning: post directory does not exists: "myheap_posts"
    Post directory has been created.
    Warning: HTML directory does not exists: "myheap_html"
    HTML directory has been created.
    Importing hkrc...
    Module not found: "hkrc"

    >>>

The |dl| command can be used to download new emails and convert them into
posts::

    >>> sh('myheap')
    >>> dl()
    Reading settings...
    Password:
    Connecting...
    Connected
    Checking...
    3 new messages found.
    Downloading...
    WARNING: author's nickname not found: Gmail Team <mail-noreply@google.com>
    WARNING: author's nickname not found: Gmail Team <mail-noreply@google.com>
    WARNING: author's nickname not found: Gmail Team <mail-noreply@google.com>
    3 new messages downloaded.
    >>> ls()
    <myheap/1> Get started with Gmail  Gmail Team <mail-noreply@google.com> (2009.10.31. 12:44)
    <myheap/2> Access Gmail on your mobile phone  Gmail Team <mail-noreply@google.com> (2009.10.31. 12:44)
    <myheap/3> Import your contacts and old email  Gmail Team <mail-noreply@google.com> (2009.10.31. 12:44)

As we can see, Heapkeeper downloaded the three "Get started" emails that were
automatically sent by Google. Unfortunately these are HTML messages, which is
not very well handled by Heapkeeper, so if we print them, we will see the HTML
code.

We can modify the posts as we like, we can even delete them::

    >>> sS(1, 'Get started')
    >>> sS(2, 'Mobile phone access')
    >>> d(3)
    >>> postdb().all().forall(lambda p: p.set_author('Google Mail Team'))
    >>> ls()
    <myheap/1> Get started  Google Mail Team (2009.10.31. 12:44)
    <myheap/2> Mobile phone access  Google Mail Team (2009.10.31. 12:44)

Date and message id
"""""""""""""""""""

These posts contain two additional fields that we have not met before: message
id ("messid" for short) and date. They can be accessed and modified from within
Heapkeeper similarly to other fields::

    >>> p(1).messid()
    '<b53945e0907251236l60da49b8t@mail.gmail.com>'
    >>> p(1).date()
    'Sat, 31 Oct 2009 04:44:02 -0700'

They are stored similarly, as well:

.. code-block:: sh

    $ cat myheap_posts/1.post | head -n 5
    Author: Google Mail Team
    Subject: Get started
    Message-Id: <b53945e0907251236l60da49b8t@mail.gmail.com>
    Date: Sat, 31 Oct 2009 04:44:02 -0700

The |ls| command already showed the date of the posts. The post contains the
date in :rfc:`2822` format, but Heapkeeper usually displays the date in local
time (e.g. the |ls| command does so). The :func:`date <hklib.Post.date>` and
:func:`date_str <hklib.Post.date_str>` methods of |Post| can be used to access
the two form of the post's date::

    >>> p(1).date()
    'Sat, 31 Oct 2009 04:44:02 -0700'
    >>> p(1).date_str()
    '2009.10.31. 12:44'

Message id and post deletion
""""""""""""""""""""""""""""

The message id is not really important to the readers and maintainers of the
heap, but it is very important to Heapkeeper itself. Just like a post id
identifies a *post*, a message id identifies an *email*. So if the |dl| command
of |hkshell| is called again, Heapkeeper will not download the emails already
downloaded, even if their posts were modified or deleted. The reason is that
the message ids of all downloaded emails are stored in the post files, even if
the post is deleted. Post 2 was deleted, but as discussed previously, the
|Post| object and the post file were not, only their content:

.. code-block:: sh

    $ cat mail_test/3.post
    Message-Id: <b53945e0907251236l2285b7faq@mail.gmail.com>
    Flag: deleted

If we invoke the |dl| command again, it will not download post 3 again:

    >>> dl()
    Reading settings...
    Password:
    Connecting...
    Connected
    Checking...
    No new messages.

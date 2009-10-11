Todo - "feature and bug tracking system"
========================================

This file is our feature and bug tracking "system". It will be replaced by the
Heapkeeper heap, which will be managed with Heapkeeper of course.

The items are in sorted in a descending order according to their priorities.

The items may have identifiers (``#1``, ``#2`` etc). Next free identifier:
``#5``

Notation
--------

* ``+``: new feature
* ``-``: bug to fix
* ``[prop]``: this should be discussed in a proposal
* ``[disc]``: this should be discussed on Hh
* ``[ongoing]``: the work on this item has been started

Todo items
----------

* **Priority**

  * supporting multiple heaps (afterwards we should clean up and upload hh)

* **Documentation**

  * continuing :doc:`architecture`
  * The :doc:`tutorial` should be rewritten (probably a separate
    *customization* page should be created). A new document called Heapkeeper
    Basics should be created.
  * words to include in the :doc:`glossary`: Heap, heapid, message id, post,
    postset, prepostset, tag
  * Explain these concepts somewhere: delegate, hkrc
  * Coding Conventions:

    * templates for documentation
    * templates for tests (``test<class>``, ``test_<method>``,
      ``test_<method>__<other stuff>``)
    * markup language for commit messages

  * Use Sphinx's ``glossary`` feature.

    From "Sphinx Markup Constructs -> Glossary":

    This directive must contain a reST definition list with terms and
    definitions. The definitions will then be referencable with the ``term``
    role.
    Example:

    .. code-block:: none

        .. glossary::

           environment
              A structure where information about all documents under the root is
              saved, and used for cross-referencing.  The environment is pickled
              after the parsing stage, so that successive runs only need to read
              and parse new and changed documents.

           source directory
              The directory which, including its subdirectories, contains all
              source files for one Sphinx project.

        ...

        See :term:`environment` for more information.

        ...

  * Documentation of modules. Documentation and revision needed:

    * hkshell: lines 529-730
    * hklib: all
    * hkcustomlib: all
    * hkutils: all

  * not important things

    * performance improvement possibilities (iterators for some PrePost and
      PostDB functions)
    * using wrappers to protect e.g. PostDB.posts()

  * move the github wiki page "email_file_format" to the rst documentation

* **Management, propaganda**

  * ``[disc]`` motto. We had two ideas, but they don't go well with the
    new name (Heapkeeper):

    * "The past is just our perception of the past."
    * "Edit the past!"

  * logo
  * setting up the public heap/public mailing list
  * own CSS theme on the homepage
  * setting up a bug tracker (current candidates: Git-Issues, Ditz or
    Heapkeeper itself)

* **Generator**

  * refactor Generator.gen_threads; now there is a lot of code duplication in
    the Generator's code
  * Generator.gen_threads should regenerate only the threads that has changed
  * Problem: some data attributes of the GeneratorOptions (e.g. ``write_toc``)
    could be moved to Section or Index. (A function as a generator option that
    can take the section into account is as good as a section option or an
    index option.)
  * ``-`` "Back to index" is buggy now, because it always goes back to the
    'index.html'
  * ``+`` Index generator: now the user defines how to show the date in
    index.html; the same could be done for other fields (e.g. the user could
    write a function that creates 'very long...' from 'very long subject')
  * Now CSS has to be copied manually to the html files. We should find another
    way to do this, in which using a custom CSS file should be as easy as now,
    but which is more convenient for the user who does not care about
    customized CSS.
  * Problem: now, if gen_posts adds an indices option, the posts will contain
    backlinks to each of these indices. It would be nicer if only those
    indices would be backlinked that really contain the post in question.

* **hkshell**

  * When ls command is invoked with no parameter, it should list the posts
    that changed last time
  * ``catch_exceptions`` option.

    Usage::

       def f():
           if ok:
               ...
           else:
               error('File not found: %s' % (filename,))

    Library::

       def error(error_message):
           if options.catch_exceptions:
               raise HkException, error_message
           else:
               options.output(error_message)
  * Using the ``$EDITOR`` environment variable instead of just using ``gvim``.

* **Tests**

  * hkshell
  * Post.load
  * hklib.Post.{set_tags, remove_tag}

    * set_tags: test unsorted lists and sets as argument

  * hklib.Post.{before, after, between}
  * doc&test: PostDB.{children, roots, threads}
  * Html.table
  * Generator.full_thread
  * Html.thread_post_header

* **Renamings**

  * CamelCase function names to lower_case in test modules
  * hklib.STAR to something

* write a ``set_version`` script that modifies the version number of
  Heapkeeper at all appropriate places (currently in hklib.py and
  conf.py)

* :func:`hklib.Post.parse`: Better exception handling during parsing. I think
  we need a HkParseException type which can be raised more conveniently during
  parsing. This type could have a constructor that gets a file desciptor and
  tries to read the file name from that. See commit 059829d for more
  information.

* hkshell: better method instead of ``touching_commands``. Maybe we should use
  decorators. (The current decorators could include this functionality.)

* hkcustomlib: refactoring DateOptions to use the Options pattern

* ``+`` ``<#2>`` Post generator:

  * ``+`` parent, children into Post HTML (easy)
  * ``+`` put prev and next links into Post HTML (the post generator should
    know about the generated index)
  * ``+`` "back to thread" link.
    HTML-id-s should be put to each thread in the index to implement this.
    Idea: would it make sense to put id-s to each post in the index? -- Csabi

* ``[prop]`` ``+`` **Post body parsing**. This should be discussed, a proposal
  should be written.

  * ``+`` creating real links form http://... text
  * ``+`` creating links from post-references. Idea:
    Original post: <<<!post: 123>>>
    In Post HTML: <a href="123.post">&lt;&lt;&lt;post: 123&gt;&gt;&gt;</a>
  * ``+`` any inline links (instead of cites):
    Original post: what about [this|http://...] thing?
    In Post HTML:  what about <a href="http://...">this</a> thing?
  * ``+`` creating flags from <<<metatext>>> (e.g. todo flag)

    * How to show the flags like "todo" in the index? Maybe they should be
      tags, and not flags?

  * ``+`` dealing with cites
  * ``+`` showing the authors of the quotes
  * ``+`` do automatic actions based on metatext? E.g. <<<!delete>>>,
    <<<!addtagtothread unix>>>
  * ``+`` formatting _underline_ and *bold* text: do we want it? (probably not)
  * ``+`` the post's HTML could contain the whole thread of the post below the
    post itself?
  * ``+`` post references for non-existent posts with explicit id-s:
    Original post1: <<<post:id=boring_stuff>>>
    Original post2: As I said in [this|post:id=boring_stuff] mail...
    Post2 in HTML:  what about <a href="http://...">this</a> thing?

* ``+`` ``<#3>`` PostSetMapDelegate::

     PostDB.postset([p1, p2, p3]).map.heapid()  -->  ['1', '2', '3']

* ``+`` ``<#4>`` PostSetGrepDelegate (precond: ``#3``): it would be similar to
  grep (but smarter of course in our domain)::

     ps.grep('unix stuff')  -->
        [('12', ['I said that unix stuff, you know']),
         ('13', ['> I said that unix stuff, you know'],
         'Yes, but your unix stuff is very'])]

  The quote could be excluded from the result of grep.

  It could be implemented with the Map delegate::

     def find_lines(regex, s):
         """Returns the lines of s that contain the regex."""
         return [ line for line in s if re.search(regex, s) ]
     def grep(ps, regex): # ps=postset
         def find_lines_in_post(regex):
             def f(post):
                 """Returns None if regex is not in the post's body; otherwise
                 returns a tuple with the heapid of the post and a list of the
                 hits"""
                 lines = find_lines(regex, post.body())
                 if lines == []:
                     return None
                 else:
                     return (post.heapid(), lines)
             return f
         return \
            [ result for result in ps.map(find_lines_in_post('unix stuff'))
              if result != None ]

     grep(ps, 'unix stuff')  -->  as in th previous example

* ``+`` Integrating the search into Vim. (precondition: ``#4``) ::

    :h setqflist()

    Hint (Vimscript code):
    call setqflist([{'filename':'12.mail', 'lnum':'4',
                     'text':'I said that unix stuff, you know'},
                    {'filename':'13.mail', 'lnum':'1',
                     'text':'> I said that unix stuff, you know'},
                    {'filename':'13.mail', 'lnum':'2',
                     'text':'Yes, but your unix stuff is very'}])

* ``+`` Model: References among posts (beyond in-reply-to)

* ``+`` tags, flags

  * ``+`` Implementing tags and flags as frozensets
  * ``+`` Tags dependencies, TagInfo class
  * ``+`` Flag: New-thead flag to indicate that the email begins a new thread.
    Post.inreplyto should return None if the post has a new-thread flag.
    Post.real_inreplyto would be the current Post.inreplyto.
  * ``+`` should the tags be case insensitive?
  * ``+`` tag aliases: py = python

* CSS

  * Try out including heapindex.css into the customized heapindex.css
  * Write about CSS into the user documentation (currently you have to make a
    symlink by hand to get it work; we should say something about this)

* ``+`` Post: cleanup functionality. Something like Post.normalize_subject,
  but with a broader scope.

  * ``+`` deleting in-reply-to if the referenced post is not in the DB

* Post, PostDB: a better system for 'touch': it should know what should be
  recalculated and what should not be. It would improve only efficiently, not
  usability.

* ``+`` Downloading emails since given date.
  Workaround: if we go to the heap account regularly and archive the emails in
  the inbox, downloading new mail will remain fast.

* ``+`` PostDB.sync: unison-like method to synchronize the data between the
  PostDB in the memory and the mail files on the disk

* Migration to Python 3

* ``+`` Inline posts: the body of the specified posts could be shown in the
  index. JavaScript (or CSS?) could be used for folding the inline posts.

* Distant future: use Django or some other web framework to manipulate the heap
  instead of hkshell.

* PostSet: method inherited from set should be reviewed whether they should be
  inherited, overriden or removed.

* Using code coverage tools

* Small performance and design improvements

  * HTML generation: we could handle lists of strings instead of strings (I'm
    not sure it would be that efficient; probably string concatenation does not
    really mean copying all the characters. The Python implementation could be
    much better, since the strings are immutable.)
  * Maybe PostDB.messid_to_heapid can be handled lazily as the other attributes
    of PostDB?

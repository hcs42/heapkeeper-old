Download page
=============

Heapkeeper repository
---------------------

.. highlight:: sh

The source code and the documentation of Heapkeeper are stored in
the `Heapkeeper repository`_, which is hosted by GitHub_. You can either
download a released version of Heapkeeper from this page or clone the
repository::

    $ git clone git://github.com/hcs42/heapkeeper.git

.. _`GitHub`: http://github.com/
.. _`Heapkeeper repository`: http://github.com/hcs42/heapkeeper/

Packaged releases
-----------------

+----------+------------+-------------+--------------------+
| version  | date       | source      | HTML documentation |
|          |            |             |                    |
+==========+============+=============+====================+
| `0.9`_   | 2010-12-31 | tgz__ zip__ | tgz__ zip__        |
+----------+------------+-------------+--------------------+
| `0.8`_   | 2010-10-17 | tgz__ zip__ | tgz__ zip__        |
+----------+------------+-------------+--------------------+
| `0.7`_   | 2010-08-20 | tgz__ zip__ | tgz__ zip__        |
+----------+------------+-------------+--------------------+
| `0.6`_   | 2010-06-01 | tgz__ zip__ | tgz__ zip__        |
+----------+------------+-------------+--------------------+
| `0.5`_   | 2010-04-25 | tgz__ zip__ | tgz__ zip__        |
+----------+------------+-------------+--------------------+
| `0.4`_   | 2010-02-19 | tgz__ zip__ | tgz__ zip__        |
+----------+------------+-------------+--------------------+
| `0.3`_   | 2009-10-11 | tgz__ zip__ | tgz__ zip__        |
+----------+------------+-------------+--------------------+
| `0.2`_   | 2009-02-17 | tgz__ zip__ |  --                |
+----------+------------+-------------+--------------------+
| `0.1`_   | 2008-10-16 | tgz__ zip__ |  --                |
+----------+------------+-------------+--------------------+

__ http://heapkeeper.org/releases/heapkeeper-0.9.tar.gz
__ http://heapkeeper.org/releases/heapkeeper-0.9.zip
__ http://heapkeeper.org/releases/heapkeeper-htmldoc-0.9.tar.gz
__ http://heapkeeper.org/releases/heapkeeper-htmldoc-0.9.zip
__ http://heapkeeper.org/releases/heapkeeper-0.8.tar.gz
__ http://heapkeeper.org/releases/heapkeeper-0.8.zip
__ http://heapkeeper.org/releases/heapkeeper-htmldoc-0.8.tar.gz
__ http://heapkeeper.org/releases/heapkeeper-htmldoc-0.8.zip
__ http://heapkeeper.org/releases/heapkeeper-0.7.tar.gz
__ http://heapkeeper.org/releases/heapkeeper-0.7.zip
__ http://heapkeeper.org/releases/heapkeeper-htmldoc-0.7.tar.gz
__ http://heapkeeper.org/releases/heapkeeper-htmldoc-0.7.zip
__ http://heapkeeper.org/releases/heapkeeper-0.6.tar.gz
__ http://heapkeeper.org/releases/heapkeeper-0.6.zip
__ http://heapkeeper.org/releases/heapkeeper-htmldoc-0.6.tar.gz
__ http://heapkeeper.org/releases/heapkeeper-htmldoc-0.6.zip
__ http://heapkeeper.org/releases/heapkeeper-0.5.tar.gz
__ http://heapkeeper.org/releases/heapkeeper-0.5.zip
__ http://heapkeeper.org/releases/heapkeeper-htmldoc-0.5.tar.gz
__ http://heapkeeper.org/releases/heapkeeper-htmldoc-0.5.zip
__ http://heapkeeper.org/releases/heapkeeper-0.4.tar.gz
__ http://heapkeeper.org/releases/heapkeeper-0.4.zip
__ http://heapkeeper.org/releases/heapkeeper-htmldoc-0.4.tar.gz
__ http://heapkeeper.org/releases/heapkeeper-htmldoc-0.4.zip
__ http://heapkeeper.org/releases/heapkeeper-0.3.tar.gz
__ http://heapkeeper.org/releases/heapkeeper-0.3.zip
__ http://heapkeeper.org/releases/heapkeeper-htmldoc-0.3.tar.gz
__ http://heapkeeper.org/releases/heapkeeper-htmldoc-0.3.zip
__ http://github.com/hcs42/heapkeeper/tarball/v0.2
__ http://github.com/hcs42/heapkeeper/zipball/v0.2
__ http://github.com/hcs42/heapkeeper/tarball/v0.1
__ http://github.com/hcs42/heapkeeper/zipball/v0.1

.. _`0.9`:

Version 0.9
^^^^^^^^^^^

- **date:** 2010-12-31
- **download:** tgz__, zip__
- **download HTML documentation:** tgz__, zip__

__ http://heapkeeper.org/releases/heapkeeper-0.9.tar.gz
__ http://heapkeeper.org/releases/heapkeeper-0.9.zip
__ http://heapkeeper.org/releases/heapkeeper-htmldoc-0.9.tar.gz
__ http://heapkeeper.org/releases/heapkeeper-htmldoc-0.9.zip

This release is mainly about refactorings and using the JsTestDriver unit
testing tool.

Major new features:

- The "postid" target was added to the search.
- hkweb can find a free port to listen on.
- hkweb is more secure by not always accepting GET requests.

Major refactorings:

- New modules hkconfig and hkemail have been extracted from hklib.
- All code of the issue tracker has been moved into the "Issue Tracker" plugin
  from the Heapkeeper core.
- hkgen.Generator was split into two classes: the part which deals with static
  HTML has been extracted into the hkgen.StaticGenerator class.
- Classes in hkweb were rearranged.
- The CSS, JavaScript and favicon files are handled uniformly throughout hkgen,
  hkweb, and the plugins.

Other major improvements:

- Documenting the hkweb module with docstrings.
- The client-server communication of hkweb has been documented.
- The JsTestDriver JavaScript unit testing tool is used for JavaScript unit tests.

Major deprecation:

- The old configuration formats are no longer supported.
- The gi() and ga() hkshell commands are no longer supported.
- The hkcustomlib module is deprecated.
- Post page generation is deprecated.

.. _`0.8`:

Version 0.8
^^^^^^^^^^^

- **date:** 2010-10-17
- **download:** tgz__, zip__
- **download HTML documentation:** tgz__, zip__

__ http://heapkeeper.org/releases/heapkeeper-0.8.tar.gz
__ http://heapkeeper.org/releases/heapkeeper-0.8.zip
__ http://heapkeeper.org/releases/heapkeeper-htmldoc-0.8.tar.gz
__ http://heapkeeper.org/releases/heapkeeper-htmldoc-0.8.zip

The main improvements of this release are hkweb features: better search, faster
post body folding, possibility to use authentication and add new child posts.

Major new features:

- New child posts can be added in hkweb.
- hkweb supports authenticating users.
- The search bar in hkweb can contain new target types: the user can search for
  posts with certain tags, posts after/before a certain date, posts on a
  certain heap, etc; and all these can be negated and combined. The "Issue
  Tracker" plugin even adds an "issue" target type.
- The search page shows the number of hits and has better unicode handling.
- The "Chat" plugin implements real-time chat (instant messaging) in hkweb.
- The "Users" plugin displays users' recent activity on hkweb pages.
- The "Custom Heap Server" plugin can be started for all heaps.

Major refactorings:

- Folding of post bodies is hkweb is 50 times faster.

Other major improvements:

- hk-dev-utils can perform automatic tests on Heapkeeper in a more convenient
  way than before.
- test.py collects test modules dynamically (they used to be hardcoded).

Major deprecation:

- Post item augmentation is no longer supported. It became unnecessary due to
  refactoring: if a post item is created, it does not need to be augmented any
  more.
- Post pages are deprecated. (Use thread pages instead.)
- Old configuration formats are deprecated. (Use the new format instead.)

.. _`0.7`:

Version 0.7
^^^^^^^^^^^

- **date:** 2010-08-20
- **download:** tgz__, zip__
- **download HTML documentation:** tgz__, zip__

__ http://heapkeeper.org/releases/heapkeeper-0.7.tar.gz
__ http://heapkeeper.org/releases/heapkeeper-0.7.zip
__ http://heapkeeper.org/releases/heapkeeper-htmldoc-0.7.tar.gz
__ http://heapkeeper.org/releases/heapkeeper-htmldoc-0.7.zip

The main improvements of this release are creating a plugin infrastructure and
adding search functionality to hkweb.

Major new features:

- Creating a plugin infrastructure. Three plugins have been created so far: the
  "Review" plugin, which can set posts to reviewed; the "Custom Heap Server"
  plugin, which shows only posts in a specified heap; and the "Issue Tracker"
  plugin, which displays the heap as a list of issues.
- Searches can be performed via hkweb.
- When editing a post in hkweb, pressing shift-enter will save the post.
- Supporting IMAP without SSL.

Major refactorings:

- Moving the Python source code into the "src" subdirectory and moving the
  CSS/JavaScript/PNG files into the "static" subdirectory.

Other major improvements:

- JavaScript unit tests were added.
- IMAP queries are more efficient and comply with :rfc:`2683` / 3.2.1.5. (Long
  Command Lines).

.. _`0.6`:

Version 0.6
^^^^^^^^^^^

- **date:** 2010-06-01
- **download:** tgz__, zip__
- **download HTML documentation:** tgz__, zip__

__ http://heapkeeper.org/releases/heapkeeper-0.6.tar.gz
__ http://heapkeeper.org/releases/heapkeeper-0.6.zip
__ http://heapkeeper.org/releases/heapkeeper-htmldoc-0.6.tar.gz
__ http://heapkeeper.org/releases/heapkeeper-htmldoc-0.6.zip

The main improvement of this release is introducing Heapkeeper's web interface.

Major new features:

- Heapkeeper has a web interface called hkweb that displays posts and allows
  editing them. Editing can be done either on the post bodies or on the raw
  post text that includes the header attributes. hkweb supports folding (hiding
  and showing the body of individual posts).
- The enew() hkshell command adds dates to the created post automatically.
- Raw blocks are recognized within post bodies and are shown in gray in the
  HTML pages.
- Links are parsed within meta text.
- The title of the HTML thread page is now the subject of the root of the
  thread.
- Links to children are displayed in the HTML pages.
- The generated HTML pages are valid XHTML pages.

Major bugfixes:

- Non-breakable space is converted to normal space in downloaded emails.
- Leading whitespace is preserved in post bodies.

.. _`0.5`:

Version 0.5
^^^^^^^^^^^

- **date:** 2010-04-25
- **download:** tgz__, zip__
- **download HTML documentation:** tgz__, zip__

__ http://heapkeeper.org/releases/heapkeeper-0.5.tar.gz
__ http://heapkeeper.org/releases/heapkeeper-0.5.zip
__ http://heapkeeper.org/releases/heapkeeper-htmldoc-0.5.tar.gz
__ http://heapkeeper.org/releases/heapkeeper-htmldoc-0.5.zip

The main improvement of this release is supporting several heaps.

Major new features:

- Heapkeeper now supports several heaps.
- The term "heapid" was abandoned as the identifiers of posts. The new terms
  are: :ref:`post index <glossary_post_index>`, :ref:`heap id
  <glossary_heap_id>`, and :ref:`post id <glossary_post_id>`.

.. _`0.4`:

Version 0.4
^^^^^^^^^^^

- **date:** 2010-02-19
- **download:** tgz__, zip__
- **download HTML documentation:** tgz__, zip__

__ http://heapkeeper.org/releases/heapkeeper-0.4.tar.gz
__ http://heapkeeper.org/releases/heapkeeper-0.4.zip
__ http://heapkeeper.org/releases/heapkeeper-htmldoc-0.4.tar.gz
__ http://heapkeeper.org/releases/heapkeeper-htmldoc-0.4.zip

The main improvement of this release is the new Generator.

Major new features:

- New generator (:mod:`hkgen.Generator`). The new generator is much more
  flexible than the old one, and has a different model of customization. It
  has many small methods, and the generator's behavior can be customized by
  overriding those that should behave differently.
- Heapids with prefixes are calculated automatically.
- Posts may have references (to other posts).
- The post file format is now "forward compatible", i.e. an older version of
  Heapkeeper will be able to handle a post file created by a newer version of
  Heapkeeper without damaging it.
- :mod:`hkshell.e` can edit several files.
- :mod:`hkshell.enew` has *author* and *parent* parameters.
- The meta texts are parsed in posts.
- A basic search functionality was added to :mod:`hkshell`.

.. _`0.3`:

Version 0.3
^^^^^^^^^^^

- **date:** 2009-10-11
- **download:** tgz__, zip__
- **download HTML documentation:** tgz__, zip__

__ http://heapkeeper.org/releases/heapkeeper-0.3.tar.gz
__ http://heapkeeper.org/releases/heapkeeper-0.3.zip
__ http://heapkeeper.org/releases/heapkeeper-htmldoc-0.3.tar.gz
__ http://heapkeeper.org/releases/heapkeeper-htmldoc-0.3.zip

This release is not primarily about new features. It improved mainly
customizability, testability, usability, documentation, and we sorted out
administrative things like license, homepage, and renamed a few things.

Major new features:

- Customization possibilities.
- Multiple index pages.
- Thread pages.
- New CSS design: colors and style from http://vim.org.
- Optional feature: pages are re-generated only when needed.
- Forward compatible handling of post files.
- Much faster IMAP downloading.

- :mod:`hkshell`:

  - Setting system.
  - Generic event handling.
  - Better handling of arguments using the ``optparse`` module.
  - Better way to provide a Python shell to the user, using the ``code``
    module.
  - New commands, e.g. enew, enew_str, ls, cat.

Major refactorings:

- Using the `Options pattern <options_pattern>`_ in
  :class:`hklib.GeneratorOptions`,
  :class:`hklib.Section`,
  :class:`hklib.Index`, etc.
- Grand Renaming 1; most importantly, the name of the program has been
  changed to Heapkeeper. (Previously it was HeapManipulator.)

Other major improvements:

- A lot of new documentation, including a :doc:`tutorial`. We moved our
  documentation to use Sphinx_. All modules except for hklib are fully
  documented with the chosen docstring format.
- A lot of new tests.
- We adapted the GPLv3 license and got the domain http://heapkeeper.org.
- We made semi-automatic scripts for packaging and uploading releases and
  documentation.

.. _`Sphinx`: http://sphinx.pocoo.org/

.. _`0.2`:

Version 0.2
^^^^^^^^^^^

- **date:** 2009-02-17
- **download:** tgz__, zip__

__ http://github.com/hcs42/heapkeeper/tarball/v0.2
__ http://github.com/hcs42/heapkeeper/zipball/v0.2

This release contains many new features, but lacks comprehensive documentation.

Major new features:

- Generating XHTML index page. The index pages may contain several sections.
- Generating (XHTML) post pages.
- Using CSS.
- Deleting posts.
- Nicknames.
- Using ini files as configuration files.
- :class:`hklib.PostSet` class added. It allows writing efficient queries about
  the post database easily.
- Dates are displayed in a convenient format.
- Posts may have tags.
- Handling cycles in the thread structure.
- New command line interface: :mod:`hkshell`.

Other major improvements:

- Adding some unit tests.

.. _`0.1`:

Version 0.1
^^^^^^^^^^^

- **date:** 2008-10-16
- **download:** tgz__, zip__

__ http://github.com/hcs42/heapkeeper/tarball/v0.1
__ http://github.com/hcs42/heapkeeper/zipball/v0.1

This release is a propotype.

Features:

- Downloading emails over IMAP.
- Storing posts in individual files.
- Generating threaded index page that contains all posts.

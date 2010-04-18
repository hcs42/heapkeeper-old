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
| `0.4`_   | 2010-02-19 | tgz__ zip__ | tgz__ zip__        |
+----------+------------+-------------+--------------------+
| `0.3`_   | 2009-10-11 | tgz__ zip__ | tgz__ zip__        |
+----------+------------+-------------+--------------------+
| `0.2`_   | 2009-02-17 | tgz__ zip__ |  --                |
+----------+------------+-------------+--------------------+
| `0.1`_   | 2008-10-16 | tgz__ zip__ |  --                |
+----------+------------+-------------+--------------------+

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
- The post file format is now "forward compaible", i.e. an older version of
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

Download
========

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
| `0.2`_   | 2009-02-17 | tgz__ zip__ |  --                |
+----------+------------+-------------+--------------------+
| `0.1`_   | 2008-10-16 | tgz__ zip__ |  --                |
+----------+------------+-------------+--------------------+

__ http://github.com/hcs42/heapkeeper/tarball/v0.2
__ http://github.com/hcs42/heapkeeper/zipball/v0.2
__ http://github.com/hcs42/heapkeeper/tarball/v0.1
__ http://github.com/hcs42/heapkeeper/zipball/v0.1

.. _`0.3`:

Version 0.3
^^^^^^^^^^^

- **date:** not yet released
- **download of preliminary version:** tgz__, zip__
- **download HTML documentation:** tgz__, zip__

__ http://heapkeeper.org/releases/heapkeeper-0.3uc.tar.gz
__ http://heapkeeper.org/releases/heapkeeper-0.3uc.zip
__ http://heapkeeper.org/releases/heapkeeper-htmldoc-0.3uc.tar.gz
__ http://heapkeeper.org/releases/heapkeeper-htmldoc-0.3uc.zip

This release is not primarily about new features. It improved mainly
customizability, testability, usability, documentation, and we sorted out
administrative things like license, homepage, and renamed a few things.

Major new features:

- Customization possibilities.
- Multiple index pages.
- Thread pages.

- :mod:`hkshell`:
  
  - Setting system.
  - Generic event handling.
  - Better handling of arguments using the ``optparse`` module.

Major refactorings:

- Using the `Options pattern <options_pattern>`_ in
  :class:`hklib.GeneratorOptions`,
  :class:`hklib.Section`,
  :class:`hklib.Index`, etc.
- Grand Renaming 1; most importantly, the name of the program has been
  changed to Heapkeeper. (Previously it was HeapManipulator.)

Other major improvements:

- A lot of new documentation. We moved our documentation to use Sphinx_.
- A lot of new tests.
- We adapted the GPLv3 license.

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

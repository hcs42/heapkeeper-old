Developer's Guide
=================

This file is a high-level introduction to the Heapmanipulator program (or
Manipulator or Hm for short) for the developer's eyes. More specific details
can be found in the documentation inside the Python code. Thanks to Python's
help system, the documentation can be accessed without opening the source code.

Development method
------------------

Development tools
^^^^^^^^^^^^^^^^^

The following programs should be installed on a developer's computer:

* Python_: executes Heapkeeper (version 2.5 or 2.6)
* Git_: version control system (we use version 1.6, but probably previous
  versions are fine)
* Sphinx_: compiles the documentation (version 0.6)
* Pygments_: used by Sphinx to syntax highlight the Python code in the
  documentation (0.8 is enough)

.. _`Python`: http://www.python.org/
.. _`Git`: http://git-scm.com/
.. _`Sphinx`: http://sphinx.pocoo.org/
.. _`Pygments`: http://pygments.org/

Reading
^^^^^^^

* `Karl Fogel: Producing Open Source Software -- How to Run a Successful Free
  Software Project <http://producingoss.com/>`_

Directory structure
-------------------

The main directories and files in the Heapmanipulator's repository:

``README``
  Usual README file.
``doc``
  Documentation files. The ``rst`` files are text files with wiki-like syntax,
  and Sphinx can be used to generate HTML or other output from them.
``doc/todo.rst``
   Our feature and bug tracking "system".
``*.py``
   Python source files -- the Manipulator itself
``heapindex.css``
   A CSS file for the generated HTML files.

Module structure
----------------

The Manipulator consists of several Python modules.

:mod:`heaplib`
   Contains general library classes and functions.
:mod:`heapmanip`
   The database and business logic of the Manipulator. Its classes can
   download, store, and manipulate posts and generate HTML from them.
:mod:`heapia`
   The interactive interface of the Manipulator.
:mod:`heapcustomlib`
   Contains functions and classes that are useful when using :mod:`heapia`.

We use unit tests to test the Manipulator's code. Each module has a module that
tests it.

:mod:`test_lib`
    Module that tests the :mod:`heaplib` module.
:mod:`test_heapmanip`
    Module that tests the :mod:`heapmanip` module.
:mod:`test_heapia`
    Module that tests the :mod:`heapia` module.
:mod:`test_heapcustomlib`
    Module that tests the :mod:`heapcustomlib` module.
:mod:`test`
    Module that tests all modules.

Todo file
---------

This file is our feature and bug tracking "system".

It contains items that may contain other items. The items may have identifiers
(#1, #2 etc). There are several kinds of items, and the type of the item is
shows before its text:
+ feature
- problem which should be fixed
* other: documentation, testing, refactoring

The items are in sorted in a descending order according to their prorities.


Glossary
--------

* delegate -
* Heap -
* heapcustom -
* heapia -
* heapid -
* manipulator -
* messid - 
* post -
* postset -
* prepostset -
* tag -


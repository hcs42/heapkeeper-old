Architecture of Heapkeeper
==========================

Module structure
----------------

Heapkeeper consists of several Python modules.

:mod:`heaplib`
   Contains general library classes and functions.
:mod:`heapmanip`
   The database and business logic of Heapkeeper. Its classes can
   download, store, and modify posts and generate HTML from them.
:mod:`heapia`
   The interactive interface of Heapkeeper.
:mod:`heapcustomlib`
   Contains functions and classes that are useful when using :mod:`heapia`.

We use unit tests to test the Heapkeeper's code. Each module has a module that
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


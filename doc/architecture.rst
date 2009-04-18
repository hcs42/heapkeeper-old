Architecture of Heapkeeper
==========================

This section describes the architecture of Heapkeeper. First it gives a
high-level overview of the system by summarizing the role of each module in a
few sentences. Then the tasks of the most important classes and functions are
explained. Finally it talks about the dependencies between the modules.

This section does not contain a detailed descriptions of the modules, classes
and functions: these descriptions can be found in the user documentation and
developer documentation of the modules.

Module structure
----------------

Heapkeeper consists of several Python modules. Each module is implemented in
the file ``<module>.py``.

:mod:`heaplib`
   Contains general library classes and functions.
:mod:`heapmanip`
   The database and business logic of Heapkeeper. Its classes can
   download, store, and modify posts and generate HTML from them.
:mod:`heapia`
   The interactive interface of Heapkeeper.
:mod:`heapcustomlib`
   Contains functions and classes that are useful for the parametrization of
   functions in other modules (especially functions of :mod:`heapmanip` and
   :mod:`heapia`).

The central modules are :mod:`heapmanip` and :mod:`heapia`. The former contains
the core functionality of Heapkeeper, while the latter provides the primary
user interface. The general library functions that are not related to the
concepts of Heapkeeper are collected in :mod:`heaplib`. Heapkeeper is a very
customizable tool: it can be customized primarily by writing Python functions.
The functions and classes of :mod:`heapcustomlib` help to implement these
custom functions.

We use unit tests to test the Heapkeeper's code, using the standard
``unittest`` module. Each module has a corresponding module that tests it.

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

Module contents
---------------

:mod:`heapmanip`
^^^^^^^^^^^^^^^^

:class:`heapmanip.Post`
    todo

:mod:`heapia`
^^^^^^^^^^^^^

:class:`heapia.Options`
    todo

Module dependencies
-------------------

Understanding which module uses which other modules may help a lot in
understanding the system itself. We say that a module depends on another if it
uses functions or classes defined in the other module.

The module dependencies are shown in the following picture:

.. image:: module_deps.png

Since :mod:`heaplib` contains general library functions, it does not use any
other modules of Heapkeeper, but all the other modules may use it. Both
:mod:`heapia` and :mod:`heapcustomlib` use :mod:`heapmanip`, since
:mod:`heapmanip` implements the data types that make the heap. :mod:`heapia`
uses :mod:`heapcustomlib` only for setting sensible default values for certain
callback functions.

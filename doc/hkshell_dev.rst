:mod:`hkshell` developer documentation
======================================

.. |Post| replace:: :class:`Post <hklib.Post>`
.. |PostDB| replace:: :class:`PostDB <hklib.PostDB>`
.. |PostSet| replace:: :class:`PostSet <hklib.PostSet>`
.. |PrePost| replace:: :ref:`PrePost <hkshell_PrePost>`
.. |PrePostSet| replace:: :ref:`PrePostSet <hkshell_PrePostSet>`
.. |Tag| replace:: :ref:`Tag <hkshell_Tag>`
.. |PreTagSet| replace:: :ref:`PreTagSet <hkshell_PreTagSet>`

See the :doc:`user documentation of hkshell <hkshell>` for the public classes
and functions.

Starting :mod:`hkshell`
-----------------------

What happens :mod:`hkshell` is invoked
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When the ``hkshell`` script is invoked (e.g. by typing ``./hkshell``), it just
executes the :mod:`hkshell` module (in such a way that it will leave the
Python interpreter open). When the :mod:`hkshell` module is invoked (e.g. by the
``hkshell`` script or by typing ``python hkshell.py``), it is executed as
a main module, so its ``__name__`` global variable is ``'__main__'``. It parses
the arguments and executes the following to statement as its last ones::

    from hkshell import *
    main(cmdl_options, args)

The first statement executes the source code of the :mod:`hkshell` module
itself again. All the global variables, functions and classes are defined
again, and the previously defined ones will be never used. (Probably they will
be collected by the garbage collector.) The ``from hkshell import *`` statement
makes it possible to use global hkshell objects (variables, functions, classes)
without having to write ``hkskell.``, such as ``d()``. Then the
:func:`hkshell.main` function is called to initialize the shell.

The drawbacks of this solution:

* It is ugly and not easy to understand.

The advangates of this solution:

* We don't need another python module (e.g. ``hkshell_starter``) to start
  hkshell.
* It works.
* It is easy for the users to use.

Functions
^^^^^^^^^

.. autofunction:: hkshell.exec_commands
.. autofunction:: hkshell.read_postdb
.. autofunction:: hkshell.init
.. autofunction:: hkshell.import_module
.. autofunction:: hkshell.main

Helper functions for commands
-----------------------------

.. autofunction:: hkshell.postset_operation

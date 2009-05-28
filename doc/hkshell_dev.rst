:mod:`hkshell` developer documentation
======================================

See the :doc:`user documentation of hkshell <hkshell>` for the public classes
and functions.

.. currentmodule:: hkshell

.. |Event| replace:: :class:`Event <hkshell.Event>`
.. |hkshell| replace:: :mod:`hkshell`
.. |Listener| replace:: :ref:`Listener <hkshell_Listener>`
.. |PostDB| replace:: :class:`PostDB <hklib.PostDB>`
.. |PostSet| replace:: :class:`PostSet <hklib.PostSet>`
.. |Post| replace:: :class:`Post <hklib.Post>`
.. |PrePostSet| replace:: :ref:`PrePostSet <hklib_PrePostSet>`
.. |PrePost| replace:: :ref:`PrePost <hklib_PrePost>`
.. |PreTagSet| replace:: :ref:`PreTagSet <hkshell_PreTagSet>`
.. |Tag| replace:: :ref:`Tag <hkshell_Tag>`
.. |UserDoc| replace:: :doc:`user documentation of hkshell <hkshell>`

Event handling
--------------

See also the :ref:`Event handling section<hkshell_Event_handling>` of the
|UserDoc|.

.. autofunction:: postset_operation

Concrete listeners
^^^^^^^^^^^^^^^^^^

.. autoclass:: ModificationListener

    **Methods:**
    
    .. automethod:: __init__
    .. automethod:: close
    .. automethod:: __call__
    .. automethod:: touched_posts

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

.. autofunction:: exec_commands
.. autofunction:: read_postdb
.. autofunction:: init
.. autofunction:: import_module
.. autofunction:: main


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
executes the :mod:`hk` module, which imports the :mod:`hkshell` module and
invokes the :func:`hkshell.parse_args` and :func:`hkshell.main` functions.
:func:`hkshell.parse_args` parses the command line options.
:func:`hkshell.main` which executes command arguments of ``hkshell``, import
the given customization modules (``hkrc`` by default), and gives the user an
interpreter.

Functions
^^^^^^^^^

.. autofunction:: exec_commands
.. autofunction:: read_postdb
.. autofunction:: init
.. autofunction:: import_module
.. autofunction:: main


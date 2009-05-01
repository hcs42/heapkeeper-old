:mod:`hkshell` user documentation
=================================

See the :doc:`developer documentation of hkshell <hkshell_dev>` for more details.

.. automodule:: hkshell

Options
-------
   
.. autoclass:: Callbacks()

.. autoclass:: Options()

Event handling
--------------

.. autofunction:: hkshell_events

Helper functions for commands *(to be moved to the developer documentation)*
----------------------------------------------------------------------------

.. autofunction:: postset_operation

Commands
--------

General commands
^^^^^^^^^^^^^^^^

.. autofunction:: h()
.. autofunction:: s()
.. autofunction:: x()
.. autofunction:: rl()
.. autofunction:: g()
.. autofunction:: ga()
.. autofunction:: dl(from_=0)

Tag manipulating commands
^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: pt(pps)
.. autofunction:: at(pps, tags)
.. autofunction:: atr(pps, tags)
.. autofunction:: rt(pps, tags)
.. autofunction:: rtr(pps, tags)
.. autofunction:: st(pps, tags)
.. autofunction:: str_(pps, tags)

Subject manipulator commands
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: pS(pps)
.. autofunction:: sS(pps, subject)
.. autofunction:: sSr(pps, subject)
.. autofunction:: capitalize_subject(post)
.. autofunction:: cS(pps)
.. autofunction:: cSr(pps)

Miscellaneous commands
^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: ls(pps)
.. autofunction:: d(pps)
.. autofunction:: dr(pps)
.. autofunction:: j(pp1, pp2)
.. autofunction:: e(pp)

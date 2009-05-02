:mod:`hkshell` user documentation
=================================

.. |Post| replace:: :class:`Post <hklib.Post>`
.. |PostDB| replace:: :class:`PostDB <hklib.PostDB>`
.. |PostSet| replace:: :class:`PostSet <hklib.PostSet>`
.. |PrePost| replace:: :ref:`PrePost <hkshell_PrePost>`
.. |PrePostSet| replace:: :ref:`PrePostSet <hkshell_PrePostSet>`
.. |Tag| replace:: :ref:`Tag <hkshell_Tag>`
.. |PreTagSet| replace:: :ref:`PreTagSet <hkshell_PreTagSet>`

See the :doc:`developer documentation of hkshell <hkshell_dev>` for private
class and functions.

.. automodule:: hkshell

Options
-------
   
.. autoclass:: Callbacks()

.. autoclass:: Options()

Event handling
--------------

.. autofunction:: hkshell_events

.. _hkshell_commands:

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

Tag manipulator commands
^^^^^^^^^^^^^^^^^^^^^^^^

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

Features
--------

.. autofunction:: on()
.. autofunction:: off()

Utilities
---------

.. autofunction:: shell_cmd
.. autofunction:: define_cmd

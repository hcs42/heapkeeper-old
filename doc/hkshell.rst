:mod:`hkshell` user documentation
=================================

See the :doc:`developer documentation of hkshell <hkshell_dev>` for private
classes and functions.

.. automodule:: hkshell

.. |Event| replace:: :class:`Event`
.. |hkshell| replace:: :mod:`hkshell`
.. |Listener| replace:: :ref:`Listener <hkshell_Listener>`
.. |PostDB| replace:: :class:`PostDB <hklib.PostDB>`
.. |PostSet| replace:: :class:`PostSet <hklib.PostSet>`
.. |Post| replace:: :class:`Post <hklib.Post>`
.. |PrePostSet| replace:: :ref:`PrePostSet <hklib_PrePostSet>`
.. |PrePost| replace:: :ref:`PrePost <hklib_PrePost>`
.. |PreTagSet| replace:: :ref:`PreTagSet <hkshell_PreTagSet>`
.. |Tag| replace:: :ref:`Tag <hkshell_Tag>`

Options
-------
   
.. autoclass:: Callbacks()

.. autoclass:: Options()

    There is an :class:`Options` object called ``hkshell.options``. The
    functions and methods of |hkshell| read the value of specific options from
    this object. The users of |hkshell| are allowed to change this object in
    order to achieve the behaviour they need.

.. _hkshell_Event_handling:

Event handling
--------------

|hkshell| uses an event handling model similar to that of many APIs.
``hkshell.listeners`` is a list that contains objects or functions, which are
called listeners or event handlers. They are called each time an event happens
in |hkshell|. An event is raised when a command is called, a command is
finished, or anything really that we want to use as an event. An event is
represented by an instance of the |Event| class, and is raised by calling the
:func:`event` function.

All :ref:`features <hkshell_features>` are implemented as event handlers. The
event handlers can depend on each other: e.g. the event handler of most
features depend on is the :class:`TouchedPostPrinterListener` event printer.
Thus this event printer is present in the ``heapia.listeners`` list by default.

.. autoclass:: Event()

    **Methods:**

    .. automethod:: __init__

.. autofunction:: event
.. autofunction:: append_listener
.. autofunction:: remove_listener
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

.. _hkshell_features:

Features
--------

..
    This text is only a comment yet; is should be formatted, modified and
    include in the normal text.
    
    Features can be turned on and off with heapia commands 'on' and 'off',
    just like this:
    
        >>> on('gen_incices')
        >>> off('gen_incices')
    
    The 'gen_indices' feature will regenerate the indices (HTML files that
    contain an index of the posts) when a mail database changed after a
    commands. Other features:
    
    * gen_indices - automatically regenerates the indices
    * gen_posts - automatically regenerates the posts
    * save - automatically saves the database
    * timer - times the commands
    * touched_post_printer - prints the list of posts that has been changed
      by the last command
    
    Every feature has a shortcut, so for example it is enough to type
    "on('gi')" instead of "on('gen_incices')".
    
.. autofunction:: on()
.. autofunction:: off()

Utilities
---------

.. autofunction:: shell_cmd
.. autofunction:: define_cmd

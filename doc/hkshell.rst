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
.. autofunction:: gi()
.. autofunction:: gt()
.. autofunction:: gp()
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
.. autofunction:: enew()

.. _hkshell_features:

Features
--------

*Features* are constructs that make high-level customization of Heapkeeper
easy. Every feature has a unique name. During the execution of Heapkeeper,
every feature has a value. (E.g. the feature called ``gen_indices`` can have
two values: ``on`` and ``off``.) The value of a feature describes how
Heapkeeper should behave in certain situations. (E.g. if the value of the
``gen_indices`` feature is ``on``, index pages will be automatically generated
after a command changed some posts.) Currently we have only boolean
(``on``/``off``) features. They can be turned on and off with |hkshell|
commands :func:`on` and :func:`off`. For example, this is how the
``gen_indices`` feature is turned on and off::

    >>> on('gen_indices')
    >>> off('gen_indices')

All features have a long and a short name. The current features are the
following:

- *gi*, *gen_indices* -- If ``on``: after executing a command that changed at
  least one post, Heapkeeper automatically regenerates the index pages.
- *gp*, *gen_posts* -- If ``on``: after executing a command, Heapkeeper
  automatically regenerates the post pages of the modified posts.
- *s*, *save* -- If ``on``: automatically saves the post database after the execution of
  commands.
- *t*, *timer* -- If ``on``: times the commands: the execution time of each
  command is printed when the command has been finished.
- *tpp*, *touched_post_printer* -- If ``on``: prints touched posts after
  commands that touched at least one post.
- *ep*, *event_printer* -- If ``on``: prints all events.

.. autofunction:: on()
.. autofunction:: off()

Utilities
---------

.. autofunction:: shell_cmd
.. autofunction:: define_cmd

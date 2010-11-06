|hkshell|
=========

.. include:: defs.hrst

.. automodule:: hkshell

Options
-------

.. autoclass:: Callbacks()

.. autoclass:: Options()

    There is an :class:`Options` object called ``hkshell.options``. The
    functions and methods of |hkshell| read the value of specific options from
    this object. The users of |hkshell| are allowed to change this object in
    order to achieve the behaviour they need.

.. _hkshell_Event_handling:

Command utilities
-----------------

.. autofunction:: hkshell_cmd
.. autofunction:: register_cmd

Event handling
--------------

|hkshell| uses an event handling model similar to that of many APIs.
``hkshell.listeners`` is a list that contains objects or functions, which are
called listeners or event handlers. They should implement the |Listener| type.
They are called each time an event happens in |hkshell|. An event is raised
when a command is called, a command is finished, or anything really that we
want to use as an event. An event is represented by an instance of the |Event|
class, and is raised by calling the :func:`event` function.

All :ref:`features <hkshell_features>` are implemented as event handlers. The
event handlers can depend on each other: e.g. the event handler of most
features depend on is the |TouchedPostPrinterListener| event printer. Thus this
event printer is present in the ``heapia.listeners`` list by default.

.. autoclass:: Event()

    **Methods:**

    .. automethod:: __init__

.. autofunction:: event
.. autofunction:: append_listener
.. autofunction:: remove_listener
.. autofunction:: add_events

Event handling utilities
^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: postset_operation

Concrete listeners
^^^^^^^^^^^^^^^^^^

.. autoclass:: ModificationListener

    **Methods:**

    .. automethod:: __init__
    .. automethod:: close
    .. automethod:: __call__
    .. automethod:: touched_posts

.. autoclass:: PostPageListener

    **Methods:**

    .. automethod:: __init__
    .. automethod:: outdated_posts_from_disk
    .. automethod:: close
    .. automethod:: __call__
    .. automethod:: outdated_post_pages

.. autofunction:: gen_indices_listener
.. autofunction:: save_listener
.. autofunction:: timer_listener
.. autofunction:: event_printer_listener

.. autoclass:: TouchedPostPrinterListener

    **Methods:**

    .. automethod:: __init__
    .. automethod:: __call__

.. autofunction:: add_touching_command

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
- *s*, *save* -- If ``on``: automatically saves the post database after the execution of
  commands.
- *t*, *timer* -- If ``on``: times the commands: the execution time of each
  command is printed when the command has been finished.
- *tpp*, *touched_post_printer* -- If ``on``: prints touched posts after
  commands that touched at least one post.
- *ep*, *event_printer* -- If ``on``: prints all events.

.. autofunction:: set_listener_feature
.. autofunction:: get_listener_feature
.. autofunction:: set_feature
.. autofunction:: features
.. autofunction:: on(feature)
.. autofunction:: off(feature)

Generic functionality
---------------------

.. autofunction:: write
.. autofunction:: gen_indices
.. autofunction:: tagset

Editing files with a text editor
--------------------------------

.. autofunction:: default_editor
.. autofunction:: editor_to_editor_list
.. autofunction:: edit_files

.. _hkshell_commands:

Commands
--------

General commands
^^^^^^^^^^^^^^^^

.. autofunction:: h()
.. autofunction:: gh()
.. autofunction:: sh()
.. autofunction:: p()
.. autofunction:: ps()
.. autofunction:: postdb()
.. autofunction:: c()
.. autofunction:: s()
.. autofunction:: x()
.. autofunction:: rl()
.. autofunction:: g()
.. autofunction:: gen_page(pps)
.. autofunction:: opp()
.. autofunction:: ls(pps=None, show_author=True, show_tags=False, show_date=True, indent=2)
.. autofunction:: cat(pps)
.. autofunction:: d(pps)
.. autofunction:: dr(pps)
.. autofunction:: j(pp1, pp2)
.. autofunction:: e(pp)
.. autofunction:: enew()
.. autofunction:: enew_str(post_string)
.. autofunction:: dl(from_=0)

Tag manipulator commands
^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: pT(pps)
.. autofunction:: aT(pps, tags)
.. autofunction:: aTr(pps, tags)
.. autofunction:: rT(pps, tags)
.. autofunction:: rTr(pps, tags)
.. autofunction:: sT(pps, tags)
.. autofunction:: sTr(pps, tags)

Subject manipulator commands
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: pS(pps)
.. autofunction:: sS(pps, subject)
.. autofunction:: sSr(pps, subject)
.. autofunction:: capitalize_subject
.. autofunction:: cS(pps)
.. autofunction:: cSr(pps)

Search commands
^^^^^^^^^^^^^^^

.. autofunction:: grep(pattern, pps=None)

.. _starting_hkshell:

Starting |hkshell|
------------------

When the ``hk.py`` script is invoked (e.g. by typing ``python hk.py``), it just
imports the :mod:`hkshell` module, and invokes the :func:`hkshell.parse_args`
and :func:`hkshell.main` functions. :func:`hkshell.parse_args` parses the
command line options. :func:`hkshell.main` executes the command arguments,
imports the given customization modules (``hkrc`` by default), and
gives the user an interpreter.

.. autofunction:: exec_commands
.. autofunction:: read_postdb
.. autofunction:: init
.. autofunction:: import_module
.. autofunction:: parse_args
.. autofunction:: main

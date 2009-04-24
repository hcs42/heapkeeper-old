Development rules
=================

These are rules that should be followed by the developers of Heapkeeper.
Developers may broke them, but not without a good reason.

Using the version control system
--------------------------------

* Run the :ref:`tests <testing>` before you *push* your changes and never push
  code whose test fail.
* There is not a strict policy about whether the developers may *commit*
  code intentionally that is not correct (e.g. in the middle of a refactoring).
  Probably the best is not commit incorrect code. (Note: it is about *commit*,
  the developers strictly should not *push* code intentionally that is not
  correct.)
* Documentation that does not document code (e.g. this page, the :doc:`todo
  <todo>` page) should be modified only on the master branch.

Commit messages
^^^^^^^^^^^^^^^

A commit message has two parts: a mandatory title and an optional description.

* The title should not be more than 50 characters.
* It is generally a good idea to begin the title with a word that describes the
  scope of the change (e.g. the name of a module or a class).
* Do not put a period after the title.
* The description should be preceded by a blank line.
* The description should not contain lines that have more than 79 characters.
* If the changes introduce incompatibilities that the users can notice (e.g.
  the format of the config file changes), it is generally worth describing
  them.

Example:

.. code-block:: none

   Doc: improved docstrings

   Two classes have been documented with docstrings and the docstring of
   two functions have been modified. The current format shall be used in
   all docstrings.

Development Rules
=================

These are rules that should be followed by the developers of Heapkeeper.
Developers may broke them, but not without a good reason.

There are rules that use the word "try". These are soft rules: the developers
should try to follow them, but it is not a big problem is they sometimes do not
succeed.

Using the version control system
--------------------------------

* Run the :ref:`tests <testing>` before you *push* your changes and never push
  code whose test fail.
* There is not a strict policy about whether the developers may *commit*
  code intentionally that is not correct (e.g. in the middle of a refactoring).
  Probably the best is not commit incorrect code. (Note: it is about *commit*,
  the developers strictly should not *push* code intentionally that is not
  correct.)
* Try to do larger independent changes in independent commits. E.g. if you add
  50 lines to the documentation and add a new class, and these have nothing to
  do with each other, it is better to have two separate commits for them. Of
  course if the documentation is about the new class, it is better to have them
  in the same commit.

Special commits
---------------

* Documentation that does not document code (e.g. this page, the :doc:`todo
  <todo>` page) should be modified only on the master branch.
* If you change the Development Rules, it must be done in a separate commit on
  the master branch with a commit message title that starts with ``DevRules:``.
  This way every developer will be able to follow easily what are the current
  rules of development.
* If you add a :doc:`todo <todo>` item, it must be done in a separate commit on
  the master branch with a commit message title that starts with ``Todo:``.
  This way every developer will be able to follow easily the current plans and
  goals of development.
* If you implement a :doc:`todo <todo>` item, try to do the implementation and
  the removal of the todo item in the same commit.
* Try to modify the :doc:`todo <todo>` items either in separate commits, or in
  commits where the reason of the modification is implemented.

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

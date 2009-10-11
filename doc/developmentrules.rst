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
* If it increases readability, it is a good idea to put code objects between
  ````` signs.

Example:

.. code-block:: none

   Doc: improved docstrings

   A class and a method have been documented with docstrings. The current
   format shall be used in all docstrings.

   The modified class is MyClass, the modified function is `is`.

Creating a release
------------------

.. highlight:: none

This section will describe our release process. ``<version>`` is the version of
Heapkeeper, it is something like ``0.3``.

#. Get into a clean state in git; a state that you want as the release. Use the
   branch ``_v<version>``

#. Make a list of the most important changes since the last release. Put these
   into ``doc/download.rst`` and commit it.

#. Update the Heapkeeper version number in the following files:

   - ``README``
   - ``hklib.py``
   - ``doc/conf.py``
   - ``doc/tutorial.rst``
   - ``doc/download.rst``

#. Make a commit. The commit message shall use this template::

    Heapkeeper v<version> released.

    <List of changes copied from download.rst>.

#. Push the changes to the GitHub repository::

    $ git push origin _v<version>

#. Let the others review the commits.

#. If everybody is satisfied, tag the commit, push the tag and merge the master::

    $ git tag v<version>
    $ git push origin v<version>
    $ git checkout master
    $ git merge v<version>
    $ git push origin master
    $ git push origin :_v<version>

#. Execute the documentation pusher and package maker scripts::

    $ scripts/pushdoc hcs@heapkeeper.org
    $ scripts/make_package
    $ scripts/pushrelease hcs@heapkeeper.org

#. Make an announcement on Freshmeat__

#. Change the new version string in the following files to ``<version>+`` (e.g.
   ``0.3+``):

   - ``README``
   - ``hklib.py``
   - ``doc/conf.py``

__ http://freshmeat.net/

Workflow
========

Policies about commits
----------------------

The following rules apply to commits in the GitHub repositories. Anyone may
have commits in their own private repositories that do not conform to these
policies; but before the commits are pushed to GitHub, they should be rebased
so that they conform.

* All commits should be correct and should contain a version of Heapkeeper that
  works correctly.
* Every test case in every commit should pass; i.e. ``test.py`` should execute
  all test cases and it should not report any failures. See also :ref:`tests
  <testing>`.
* :ref:`pylint` should not give any warning in any commit that is not disabled
  in the ``pylintrc`` file of the corresponding commit; i.e.
  ``hk-dev-utils/hk_pylint`` should not print anything.
* Do independent changes in independent commits, but closely related changes in
  the same commit. As Karl Fogel wrote in his :doc:`book <reading>`: "have each
  commit be a single logical change". You can read more here__. Examples from
  Heapkeeper development:

  * If you add some documentation and add a new class, and these have not much
    to do with each other, create two separate commits for them.
  * If you add a new method to a class, write documentation and unit tests for
    the method, create one commit for all of these. It is nice to review a
    commit when both the documentation and the unit tests for the change are in
    the commit.
  * If several totally independent source code lines are modified in order to
    get rid of :ref:`pylint` warnings, these should be in one commit. The parts
    of the source code that were modified may have nothing to do with each
    other, but the commit is still logically a single change because of the one
    common objective.

See the conventions about commit messages :ref:`here
<commit_message_conventions>`.

__ http://producingoss.com/en/releases-and-daily-development.html

Developing code and committing it to the local repository
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Write the code (``*.py``) and the unit test (in ``test_*.py``) in parallel.
#. Execute :ref:`pylint` to find problems::

    $ hk-dev-utils/hk_pylint

#. Execute the unit test suite including the test you just wrote::

    $ ./test.py

#. Try out the Generator::

    $ ./hk.py --noshell 'g()'

#. Document your modifications by writing docstrings.
#. Check that the docstrings are correct by generating the HTML documentation
   and viewing it in a browser::

    $ cd doc
    $ make html
    $ <your browser of choice> _build/html/modules.html

#. Check that your modifications does not include anything you don't want::

    $ git diff

#. Commit your modifications::

    $ git commit -av

Pushing to your GitHub repository
---------------------------------

#. Fetch commits of other developers, e.g.::

    git remote prune other_repo
    git fetch other_repo

#. Rebase your branch if needed.
#. Run through the commits to be pushed using :ref:`margitka`.
#. Run the unit test suite once again on all commits to be pushed::

    $ hk-dev-utils/test_commits [COMMIT_1] [COMMIT_2] ...

#. Check that the generated HTML pages were not modified using
   ``hk-dev-utils/testhtml``. Probably you should write a wrapper around it as I
   did. I invoke my wrapper this way::

    $ hcs/testhtml [COMMIT_1] [COMMIT_2] ...

#. Check that post downloading works.

#. Push the changes::

    $ git push origin <branch>

Creating a new module
---------------------

#. Create the source module (``src/<newmodule>.py``) and the test module
   (``src/test_<newmodule>.py``). Copy the copyright notice into both.
#. Create the documentation page (``doc/<newmodule>.rst``).
#. Update ``doc/defs.hrst`` with a macro for the new module.
#. Update ``doc/modules.rst``.
#. Update ``doc/architecture.rst`` with the description of the new module and
   ``doc/module_deps.png``::

    $ cd doc
    $ <your editor of choice> module_deps.dot
    $ dot -Tpng -o images/module_deps.png module_deps.dot

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
   - ``src/hklib.py``
   - ``doc/conf.py``
   - ``doc/tutorial.rst``
   - ``doc/download.rst``

#. Make a commit. The commit message shall use this template::

    Heapkeeper v<version> released.

    [v<version>]

    <List of changes copied from download.rst>.

#. Execute the package maker script and push the package to the homepage::

    $ hkdu-make-package
    $ hkdu-pushrelease info@heapkeeper.org

#. Download the uploaded package and perform the steps in the :doc:`tutorial`.

#. Push the changes to the GitHub repository::

    $ git push origin _v<version>

#. Send an email to the Heapkeeper Heap. Let the others review the commits.

#. If everybody is satisfied, tag the commit, push the tag::

    $ git tag v<version>
    $ git push origin v<version>

#. Push the new documentation to the home page::

    $ cd doc; make clean && make html; cd ..
    $ hkdu-pushdoc info@heapkeeper.org

#. Check out ``_master`` and fast forward it to the new release::

    $ git checkout _master
    $ git merge v<version>

#. Change the new version string in the following files to ``<version>+`` (e.g.
   ``0.3+``):

   - ``README``
   - ``hklib.py``
   - ``doc/conf.py``

#. Commit it into ``_master``, and use the following commit message::

    Heapkeeper v<version>+ first commit

    [v<version>]

#. Fast forward ``master`` to ``_master``. Push both branches, and remove
   branch ``_v<version>``::

    $ git checkout master
    $ git merge _master
    $ git checkout _master
    $ git push origin master _master
    $ git push origin :_v<version>

#. Send an email to the Heapkeeper Heap. Make an announcement on Freshmeat__.

__ http://freshmeat.net/projects/heapkeeper

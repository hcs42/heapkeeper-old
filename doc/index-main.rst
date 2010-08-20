Heapkeeper
==========

.. toctree::
   :hidden:

   usersguide
   developersguide
   status

**Heapkeeper is a program to store, modify and display email archives,
especially mailing list archives.** "Modifying" means that the archive is not
really an archive, rather it is a living document like a wiki: it can be
modified (hopefully improved) by collaborators.

Emails (that are e.g. sent to a mailing list) are downloaded by Heapkeeper.
After an email is downloaded, it is called a *post*. Posts are stored in
Heapkeeper's databases, which are called *heaps*. (One heap corresponds to one
mailing list.) A heap is stored as a set of text files; each file contains one
post. Posts can be viewed and changed either using Heapkeeper's web interface,
or using its console interface, or by directly reading/modifying the text files
in which the posts are stored. Posts are organized in threads, as emails in
mailing list archives usually are. Posts may have tags as well. When modifying
the heap, the content of the posts can be modified, threads can be
restructured, tags can be added; or really anything can be done. If
Heapkeeper's web interface or console interface does not support the kind of
view that is to be shown or the kind of modification that is to be performed,
the users have several options. They can either write a plugin for Heapkeeper's
web interface using Python and JavaScript; or they can write a custom console
command using Python; or they can just traverse/modify directly the files that
store the posts.

Features
--------

Currently Heapkeeper has the following features:

* **Storing posts in text files**. These are human readable files with a format
  that is similar to the standard email file format (:rfc:`2822`).
* **Downloading new emails** via the IMAP SSL protocol.
* **Console interface** with commands to modify the heap. This is actually a
  Python shell with some Heapkeeper-specific functions added. Have a look at
  the console interface :ref:`here <screenshots_hkshell>`.
* **Web interface** that allows viewing and editing the posts. Currently this
  is designed to be executed locally (by default it can be accessed as
  ``http://localhost:8080/`` in the browser), because we have not yet
  implemented authentication so anyone who accesses the page can do any
  modification to the posts. The web interface can show an index page with all
  posts, a thread page with only posts in a given thread, and it also has a
  search functionality where it shows the posts with the given search terms.
  All of these pages display the posts structured into threads. See
  screenshots of the web interface :ref:`here <screenshots_pages>`.
* **Generating static HTML pages**. Have a look at examples of generated pages
  here__.

__ http://heapkeeper-heap.github.com

We plan to improve the web interface in the future. It could be run on a server
as a web application: it would download new emails from the mailings lists
automatically, it would authenticate the users, and it would use a version
control system to version control the posts.

Quick information
-----------------

* **License**: Heapkeeper is distributed under GPLv3_.
* **Download**: The released versions can be downloaded from the :doc:`download
  page <download>`. The source code and the documentation is stored in the
  `Heapkeeper repository`_, which is hosted by GitHub_, and can be used with
  the Git_ version control system.
* **Installation**: Heapkeeper requires Python_ 2.5, 2.6 or 2.7 installed;
  otherwise it can be executed without any specific installation steps.
* **Documentation**: The home page and the documentation is written in
  reStructuredText_ format. Sphinx_ is used to generate HTML pages.
* **Status**: Heapkeeper is in a usable form now, although there are many
  things which could be done to make it more convenient. Read more on the
  project's :doc:`Status <status>` page. Heapkeeper is under active
  development; look at the `commit history`__ or the `impact graph`__ of the
  repository.
* **Contact**: We have a
  :email:`mailing list, <heapkeeper-heap@googlegroups.com>` and a :ref:`heap
  based on that mailing list <heapkeeper_heap>`.

.. .. The :email:`...` object should not be broken into several lines, because
.. .. then it does not work.

.. _GPLv3: http://gplv3.fsf.org/
.. _`Git`: http://git-scm.com/
.. _`GitHub`: http://github.com/
.. _`Heapkeeper repository`: http://github.com/hcs42/heapkeeper/
.. _`Python`: http://www.python.org/
.. _`reStructuredText`: http://docutils.sourceforge.net/rst.html
.. _`Sphinx`: http://sphinx.pocoo.org/
__ http://github.com/hcs42/heapkeeper/commits/master
__ http://github.com/hcs42/heapkeeper/graphs/impact

Documentation
-------------

* :doc:`usersguide`

  * :doc:`tutorial`
  * :doc:`customization` -- under construction
  * :doc:`glossary`

* :doc:`developersguide`

  * :doc:`development`
  * :doc:`codingconventions`
  * :doc:`keyprinciples`
  * :doc:`patterns`
  * :doc:`architecture`
  * :doc:`modules`

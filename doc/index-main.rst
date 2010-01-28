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

Emails (that are e.g. sent to a mailing list) are downloaded by
Heapkeeper. After an email is downloaded, it is called a *post*. Posts are
stored in Heapkeeper's database, which is called *the heap*. The heap is
stored in a set of text files; each file contains one post. Posts can be
changed either from Heapkeeper's console interface or by
directly modifying the text files in which the posts are stored. Posts are
organized in threads, as emails in mailing list archives usually are. Posts may
have tags as well. When modifying the heap, the content of the posts can be
modified, threads can be restructured, tags can be added; or really anything
can be done. If Heapkeeper's console interface does not support the kind
of modification that is to be performed, the user can either write a custom
command using Python, or modify directly the files that store the posts. HTML
*index pages* can be generated to display certain views of the heap. One of the
most simple indices is just showing all posts in a threaded structure. When the
user clicks on a post in an index in the browser, the browser will display the
HTML generated from the corresponding post.

Features
--------

Currently Heapkeeper is a console tool with the following features:

* Storing posts in text files. These are human readable files with a format
  that is similar to the standard email file format (:rfc:`2822`).
* Downloading new emails via the IMAP SSL protocol.
* Console interface with commands to modify the heap. This is actually a
  Python shell with functions. See the available commands :doc:`here
  <hkshell>`.
* Generating HTML pages from the heap. There are two kinds of HTML page: index
  pages and post pages. Index pages show the structure of the threads. Post
  pages contain one post.

We plan to implement a web version of the tool in the future. It would download
new emails automatically, and it would have a web interface for modifying
the heap.

Quick information
-----------------

* **License**: Heapkeeper is distributed under GPLv3_.
* **Download**: The released versions can be downloaded from the :doc:`download
  page <download>`. The source code and the documentation is stored in the
  `Heapkeeper repository`_, which is hosted by GitHub_, and can be used with
  the Git_ version control system.
* **Installation**: Heapkeeper requires Python_ 2.5 or 2.6 installed; otherwise
  it can be executed without any specific installation steps.
* **Documentation**: The home page and the documentation is written in
  reStructuredText_ format. Sphinx_ is used to generate HTML pages.
* **Status**: Heapkeeper is in a usable form now, although there are many
  things which could be done to make it more convenient. Read more on the
  project's :doc:`Status <status>` page. Heapkeeper is under active
  development; look at the `commit history`__ or the `impact graph`__ of the
  repository.
* **Contact**:
  :email:`Csaba Hoch, <http://hcs42.github.com>`
  :email:`Attila Nagy <mailto:nagy.attila.1984@gmail.com>`

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
  * :doc:`developmentrules`
  * :doc:`codingconventions`
  * :doc:`keyprinciples`
  * :doc:`patterns`
  * :doc:`architecture`
  * :doc:`modules`
  * :doc:`todo`

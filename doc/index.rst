Heapkeeper
==========

.. toctree::
   :hidden:

   index-main
   screenshots
   download
   usersguide
   developersguide

.. image:: images/banner.png
      :align: center

.. image:: images/workflow.png
      :align: center

*Heapkeeper* is a program to store, modify and display email archives,
especially mailing list archives.

.. Emails (that are e.g. sent to a mailing list) are downloaded by
.. Heapkeeper. After an email is downloaded, it is called a *post*. Posts are
.. stored in Heapkeeper's database, which is called *the heap*. The heap is
.. stored in a set of text files; each file contains one post. Posts can be
.. changed either from Heapkeeper's console interface or by
.. directly modifying the text files in which the posts are stored. Posts are
.. organized in threads, as emails in mailing list archives usually are. Posts may
.. have tags as well. When modifying the heap, the content of the posts can be
.. modified, threads can be restructured, tags can be added; or really anything
.. can be done. If Heapkeeper's console interface does not support the kind
.. of modification that is to be performed, the user can either write a custom
.. command using Python, or modify directly the files that store the posts. HTML
.. *index pages* can be generated to display certain views of the heap. One of the
.. most simple indices is just showing all posts in a threaded structure. When the
.. user clicks on a post in an index in the browser, the browser will display the
.. HTML generated from the corresponding post.

.. Currently Heapkeeper is a console tool with the following features:
.. 
.. * Storing posts in text files. These are human readable files with a format
..   that is similar to the standard email file format (:rfc:`2822`).
.. * Downloading new emails via the IMAP SSL protocol.
.. * Console interface with commands to modify the heap. This is actually a
..   Python shell with functions. See the available commands :doc:`here <hkshell>`.
.. * Generating HTML pages from the heap. There are two kinds of HTML page: index
..   pages and post pages. Index pages show the structure of the threads. Post
..   pages contain one post.
.. 
.. We plan to implement a web version of the tool in the future. It would download
.. new emails automatically, and it would have a web interface for modifying
.. the heap.

* **Detailed introduction**: You can find more information :doc:`here <index-main>`.
* **Screenshots**: You can find screenshots :doc:`here <screenshots>`.
* **Download**: The released versions of Heapkeeper can be downloaded from the
  :doc:`download page <download>`.
* **Tutorial**: Get started with :doc:`this <tutorial>` illustrated guide in minutes.
* **Contact**:
  Csaba Hoch (``csaba.hoch@gmail.com``),
  Attila Nagy (``nagy.attila.1984@gmail.com``)


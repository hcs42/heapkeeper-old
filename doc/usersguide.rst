User's Guide
============

.. toctree::

   tutorial
   hkshell
   glossary

Heap is a data structure that consists of posts. It is primarily represented in
mailfiles, but HTML files may be generated from them. The posts have fields,
e.g. author, subject, tags, flags, a field that describes the previous post.
The generated HTML displays the posts in a threaded structure.

The Heapkeeper is a program written is Python that can modify this
data structure: e.g. it can download new posts from an IMAP server, modify the
posts, and generate HTML files.

Heapkeeper consists of several modules that are described in the
Developer guide. The heapia module is the interactive interface of
Heapkeeper, that's designed for end-users. The User Guide will explain how
to use Heapkeeper via the heapia module.

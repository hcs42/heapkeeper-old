:mod:`hklib` user documentation
===============================

See the :doc:`developer documentation of hklib <hklib_dev>` for more
details.

-------------------------------------------------------------------------------

.. automodule:: hklib

Post
----

.. autoclass:: Post

    **Methods:**

    .. method:: subject
    .. method:: set_subject
    .. method:: real_subject
    .. method:: set_body

PostDB
------

.. class:: PostDB

PostSet
-------

.. class:: PostSet

EmailDownloader
---------------

.. class:: EmailDownloader

Section, Index
--------------

.. class:: Section

.. class:: Index

Html
----
   
.. autoclass:: Html

    **Methods:**

    .. automethod:: enclose

Generator
---------

.. class:: GeneratorOptions

.. autoclass:: Generator
    
    **Methods:**

    .. automethod:: __init__
    .. automethod:: post
    .. automethod:: index_toc
    .. automethod:: post_summary
    .. automethod:: post_summary_end
    .. automethod:: thread
    .. automethod:: section
    .. automethod:: gen_indices
    .. automethod:: gen_posts

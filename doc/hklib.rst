|hklib|
=======

.. include:: defs.hrst

.. automodule:: hklib

Logging
-------

.. autofunction:: default_log_fun
.. autofunction:: set_log
.. autofunction:: log


Post
----

.. autoclass:: Post

    **Methods:**

    .. automethod:: __init__
    .. automethod:: from_str
    .. automethod:: from_file
    .. automethod:: create_empty
    .. automethod:: touch
    .. automethod:: is_modified
    .. automethod:: add_to_postdb
    .. automethod:: heapid
    .. automethod:: author
    .. automethod:: set_author
    .. automethod:: real_subject
    .. automethod:: subject
    .. automethod:: set_subject
    .. automethod:: messid
    .. automethod:: set_messid
    .. automethod:: parent
    .. automethod:: set_parent
    .. automethod:: date
    .. automethod:: set_date
    .. automethod:: timestamp
    .. automethod:: datetime
    .. automethod:: _recalc_datetime
    .. automethod:: date_str
    .. automethod:: before
    .. automethod:: after
    .. automethod:: between
    .. automethod:: tags
    .. automethod:: set_tags

    .. automethod:: meta_dict
    .. automethod:: _recalc_meta_dict

PostDB
------

.. class:: PostDB

    **Methods:**

    .. automethod:: walk_thread

PostItem
^^^^^^^^

.. autoclass:: PostItem

    **Methods:**

    .. automethod:: __init__
    .. automethod:: copy
    .. automethod:: __str__

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

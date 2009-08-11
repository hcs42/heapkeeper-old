|hklib|
=======

.. include:: defs.hrst

.. automodule:: hklib

Logging
-------

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
..    .. automethod:: add_tag
..    .. automethod:: remove_tag
..    .. automethod:: has_tag
..    .. automethod:: has_tag_from
..    .. automethod:: flags
..    .. automethod:: set_flags
..    .. automethod:: is_deleted
..    .. automethod:: delete
..    .. automethod:: body
..    .. automethod:: set_body
..    .. automethod:: body_contains
..    .. automethod:: parse
..    .. automethod:: parse_header
..    .. automethod:: create_header
..    .. automethod:: write
..    .. automethod:: save
..    .. automethod:: load
..    .. automethod:: postfilename
..    .. automethod:: htmlfilebasename
..    .. automethod:: htmlfilename
..    .. automethod:: htmlthreadbasename
..    .. automethod:: htmlthreadfilename
..    .. automethod:: postfile_exists
..    .. automethod:: __eq__
..    .. automethod:: __repr__
..    .. automethod:: remove_google_stuff
..    .. automethod:: parse_subject
..    .. automethod:: normalize_subject

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

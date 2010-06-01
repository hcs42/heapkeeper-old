|hklib|
=======

.. include:: defs.hrst

.. automodule:: hklib

Post
----

.. autoclass:: PostNotFoundError

    **Methods:**

    .. automethod:: __init__
    .. automethod:: __str__

.. autoclass:: Post

    **Methods:**

    .. automethod:: is_post_id
    .. automethod:: assert_is_post_id
    .. automethod:: unify_post_id
    .. automethod:: parse_header
    .. automethod:: create_header
    .. automethod:: parse
    .. automethod:: __init__
    .. automethod:: from_str
    .. automethod:: from_file
    .. automethod:: create_empty
    .. automethod:: touch
    .. automethod:: is_modified
    .. automethod:: post_id
    .. automethod:: heap_id
    .. automethod:: post_index
    .. automethod:: post_id_str
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
    .. automethod:: add_tag
    .. automethod:: remove_tag
    .. automethod:: has_tag
    .. automethod:: has_tag_from
    .. automethod:: flags
    .. automethod:: set_flags
    .. automethod:: is_deleted
    .. automethod:: delete
    .. automethod:: meta_dict
    .. automethod:: _recalc_meta_dict
    .. automethod:: body
    .. automethod:: set_body
    .. automethod:: body_contains
    .. automethod:: write
    .. automethod:: write_str
    .. automethod:: read
    .. automethod:: read_str
    .. automethod:: postfile_str
    .. automethod:: save
    .. automethod:: load
    .. automethod:: postfilename
    .. automethod:: htmlfilebasename
    .. automethod:: htmlfilename
    .. automethod:: htmlthreadbasename
    .. automethod:: htmlthreadfilename
    .. automethod:: postfile_exists
    .. automethod:: add_to_postdb
    .. automethod:: __eq__
    .. automethod:: __ne__
    .. automethod:: __lt__
    .. automethod:: __gt__
    .. automethod:: __le__
    .. automethod:: __ge__
    .. automethod:: __repr__
    .. automethod:: remove_google_stuff
    .. automethod:: parse_subject
    .. automethod:: normalize_subject

PostDB
------

.. autoclass:: PostDBEvent

    **Methods:**

    .. automethod:: __init__(type, post=None)
    .. automethod:: __str__

.. autoclass:: PostDB

    **Methods:**

    .. automethod:: __init__
    .. automethod:: add_post_to_dicts
    .. automethod:: remove_post_from_dicts
    .. automethod:: load_heap
    .. automethod:: add_heap
    .. automethod:: set_html_dir
    .. automethod:: get_heaps_from_config
    .. automethod:: read_config
    .. automethod:: notify_listeners
    .. automethod:: touch
    .. automethod:: notify_changed_messid
    .. automethod:: has_post_id
    .. automethod:: heap_ids
    .. automethod:: has_heap_id
    .. automethod:: next_post_index
    .. automethod:: invalidate_next_post_index_cache
    .. automethod:: real_posts
    .. automethod:: posts
    .. automethod:: _recalc_posts
    .. automethod:: postset
    .. automethod:: post_by_post_id
    .. automethod:: post_by_messid
    .. automethod:: post
    .. automethod:: save
    .. automethod:: reload
    .. automethod:: add_new_post
    .. automethod:: all
    .. automethod:: _recalc_all
    .. automethod:: threadstruct
    .. automethod:: parent
    .. automethod:: root
    .. automethod:: children
    .. automethod:: _recalc_threadstruct
    .. automethod:: iter_thread
    .. automethod:: walk_thread
    .. automethod:: cycles
    .. automethod:: has_cycle
    .. automethod:: _recalc_cycles
    .. automethod:: walk_cycles
    .. automethod:: roots
    .. automethod:: _recalc_roots
    .. automethod:: threads
    .. automethod:: _recalc_threads
    .. automethod:: move
    .. automethod:: postfile_name
    .. automethod:: html_dir

PostItem
^^^^^^^^

.. autoclass:: PostItem

    **Methods:**

    .. automethod:: __init__
    .. automethod:: copy
    .. automethod:: __str__
    .. automethod:: __eq__

PostSet
-------

.. autoclass:: PostSet

    .. automethod:: __init__
    .. automethod:: empty_clone
    .. automethod:: copy
    .. automethod:: _to_set
    .. automethod:: is_set
    .. automethod:: __getattr__
    .. automethod:: expb
    .. automethod:: expf
    .. automethod:: exp
    .. automethod:: sorted_list
    .. automethod:: construct

.. autoclass:: PostSetForallDelegate

    .. automethod:: __init__
    .. automethod:: __call__
    .. automethod:: __getattr__

.. autoclass:: PostSetCollectDelegate

    .. automethod:: __init__
    .. automethod:: __call__
    .. automethod:: is_root
    .. automethod:: __getattr__


EmailDownloader
---------------

.. autoclass:: EmailDownloader

    .. automethod:: __init__
    .. automethod:: connect
    .. automethod:: close
    .. automethod:: parse_email
    .. automethod:: create_post_from_email
    .. automethod:: download_new

Generator
---------

.. autoclass:: GeneratorOptions

    .. automethod:: __init__

Configuration objects
---------------------

.. autofunction:: unify_config
.. autofunction:: unify_format_1
.. autofunction:: convert_nicknames_f12_to_f3
.. autofunction:: convert_heaps_f2_to_f3
.. autofunction:: unify_format_2
.. autofunction:: unify_nicknames
.. autofunction:: unify_server
.. autofunction:: unify_format_3

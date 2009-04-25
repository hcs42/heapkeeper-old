:mod:`heapmanip` user documentation
===================================

See the :doc:`developer documentation of heapmanip <heapmanip_dev>` for more
details.

-------------------------------------------------------------------------------

.. automodule:: heapmanip

Html
----
   
.. autoclass:: Html

    **Methods:**

    .. automethod:: enclose

.. class:: Post

    **Methods:**

    .. method:: subject
    .. method:: set_subject
    .. method:: real_subject

.. class:: MailDB
.. class:: PostSet
.. class:: Server
.. class:: Section
.. class:: Index
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

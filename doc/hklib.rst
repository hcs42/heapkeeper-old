:mod:`hklib` user documentation
===============================

.. |Post| replace:: :class:`Post`
.. |PostDB| replace:: :class:`PostDB`
.. |PostSet| replace:: :class:`PostSet`
.. |Section| replace:: :class:`Section`
.. |Index| replace:: :class:`GeneratorOptions`
.. |GeneratorOptions| replace:: :class:`GeneratorOptions`
.. |Generator| replace:: :class:`Generator`
.. |PrePost| replace:: :ref:`PrePost <hklib_PrePost>`
.. |PrePostSet| replace:: :ref:`PrePostSet <hklib_PrePostSet>`
.. |Tag| replace:: :ref:`Tag <hkshell_Tag>`
.. |PreTagSet| replace:: :ref:`PreTagSet <hkshell_PreTagSet>`

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

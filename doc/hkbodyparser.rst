|hkbodyparser|
==============

.. include:: defs.hrst

.. automodule:: hkbodyparser

Classes that represent the body
===============================

.. autoclass:: Segment

    **Methods:**

    .. automethod:: __init__
    .. automethod:: __eq__
    .. automethod:: is_similar
    .. automethod:: __str__
    .. automethod:: get_prepost_id_str
    .. automethod:: set_prepost_id_str

.. autoclass:: Body

    **Methods:**

    .. automethod:: __init__
    .. automethod:: __str__

Parser functions
================

.. autofunction:: segment_type_is
.. autofunction:: segment_condition
.. autofunction:: ensure_similar
.. autofunction:: parse_line_part
.. autofunction:: parse_line
.. autofunction:: parse

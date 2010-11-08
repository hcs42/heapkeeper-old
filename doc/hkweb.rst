|hkweb|
=======

.. include:: defs.hrst

.. automodule:: hkweb

HTTP basic authentication
-------------------------

.. autofunction:: default_deny
.. autofunction:: make_auth
.. autofunction:: make_minimal_verifier
.. autofunction:: account_verifier
.. autofunction:: enable_authentication

Utility functions
-----------------

.. autofunction:: get_web_args
.. autofunction:: last

Generator classes
-----------------

.. autoclass:: WebGenerator

    **Methods:**

    .. automethod:: __init__
    .. automethod:: print_html_head_content
    .. automethod:: print_postitem_link
    .. automethod:: print_searchbar
    .. automethod:: print_js_links
    .. automethod:: print_additional_header
    .. automethod:: print_additional_footer

.. autoclass:: IndexGenerator

    **Methods:**

    .. automethod:: __init__
    .. automethod:: print_main

.. autoclass:: PostPageGenerator

    **Methods:**

    .. automethod:: __init__
    .. automethod:: set_post_id
    .. automethod:: print_post_page
    .. automethod:: get_postsummary_fields_inner
    .. automethod:: print_hkweb_summary_buttons
    .. automethod:: print_postitem_body
    .. automethod:: print_main

.. autoclass:: SearchPageGenerator

    **Methods:**

    .. automethod:: __init__
    .. automethod:: print_search_page_core
    .. automethod:: print_search_page

.. autoclass:: PostBodyGenerator

    **Methods:**

    .. automethod:: __init__
    .. automethod:: print_post_body

Webserver classes
-----------------

.. autoclass:: WebpyServer

    **Methods:**

    .. automethod:: __init__

.. autoclass:: HkPageServer

    **Methods:**

    .. automethod:: __init__
    .. automethod:: serve_html

.. autoclass:: Index

    **Methods:**

    .. automethod:: __init__
    .. automethod:: GET

.. autoclass:: Post

    **Methods:**

    .. automethod:: __init__
    .. automethod:: GET

.. autoclass:: Search

    **Methods:**

    .. automethod:: __init__
    .. automethod:: main
    .. automethod:: get_posts
    .. automethod:: GET
    .. automethod:: POST

Helper servers
--------------

.. autoclass:: ShowJSon

    **Methods:**

    .. automethod:: __init__
    .. automethod:: GET
    .. automethod:: POST

.. autoclass:: RawPostBody

    **Methods:**

    .. automethod:: __init__
    .. automethod:: GET

.. autoclass:: RawPostText

    **Methods:**

    .. automethod:: __init__
    .. automethod:: GET

AJAX servers
------------

.. autoclass:: AjaxServer

    **Methods:**

    .. automethod:: __init__
    .. automethod:: POST

.. autoclass:: SetPostBody

    **Methods:**

    .. automethod:: __init__
    .. automethod:: execute

.. autoclass:: GetPostBody

    **Methods:**

    .. automethod:: __init__
    .. automethod:: execute

.. autoclass:: SetRawPost

    **Methods:**

    .. automethod:: __init__
    .. automethod:: execute

.. autoclass:: Fetch

    **Methods:**

    .. automethod:: GET

Main server class
-----------------

.. autoclass:: Server

    **Methods:**

    .. automethod:: __init__
    .. automethod:: run

Interface functions
-------------------

.. autofunction:: start
.. autofunction:: insert_urls

Customization
=============

This page is under construction.

The content of this page will be the following:

* ``hk.conf`` configuration file
* introduction for ``hk.rc``
* customizing the index pages and post pages

  * custom CSS
  * using custom indices (``hk.rc``)
  * using custom post summaries  (``hk.rc``)

* defining new commands (``hk.rc``)
* defining new event handlers (``hk.rc``)
* customizing :class:`heapia.Options` and :class:`heapia.Callbacks` (``hk.rc``)

.. .. Customizing the interface
.. .. -------------------------
.. ..
.. .. hkshell can be customized by creating a Python module called heapcustom. If the
.. .. appropriate callback functions are defined here, they will be used by hkshell
.. .. instead of the default behaviour.
.. ..
.. .. E.g. the following ``heapcustom.py`` changes the arguments of the
.. .. HTML-generator so that it includes the table of contents in the generated HTML
.. .. and omits the dates. ::
.. ..
.. ..     import hklib
.. ..
.. ..     def gen_index_html(maildb):
.. ..         g = hklib.Generator(maildb)
.. ..         g.index_html(write_toc=True, write_date=False)
.. ..
.. .. The same can be done by hand from the Heapkeeper's interactive shell,
.. .. without creating ``heapcustom`` module::
.. ..
.. ..     >>> def my_gen_index_html(maildb):
.. ..     ...     g = hklib.Generator(maildb)
.. ..     ...     g.index_html(write_toc=True, write_date=False)
.. ..     ...
.. ..     >>> set_callback('gen_index_html', my_gen_index_html)
.. ..
.. .. If you want to use another editor (e.g. console Vim instead of GVim), put these
.. .. into the ``heapcustom.py``::
.. ..
.. ..     import subprocess
.. ..
.. ..     def edit_default(file):
.. ..         subprocess.call(['vim', file])
.. ..         return True
.. ..
.. .. See module :mod:`heapcustom-csabahoch` as an example.
.. ..
.. .. Using the interface without Python shell
.. .. ----------------------------------------
.. ..
.. .. .. highlight:: sh
.. ..
.. .. The interface can be also used without interaction. Just call the hkshell module
.. .. and give the commands as arguments. E.g. the following line typed into a Unix
.. .. shell will download the new mail and regenerate the HTML files::
.. ..
.. ..     $ python hkshell.py 'dl()' 'ga()'  # dl = download, ga = generate all HTML

Status
------

.. include:: defs.hrst

This page describes the status of the project's components.

- Source code: Heapkeeper is in a usable form now, although there are many
  things which could be done to make it more convenient. The source code is
  constantly in a good shape, all commits in the repository since May should
  work fine.
- Tests: we aim for 100% code coverage. We have currently 74% statement
  coverage (measured with ``coverage.py``). We have 3152 lines of test code
  for 4698 lines of normal code (not counting the issue tracker and the
  hkrcs). All test pass in all commits since May 2009.
- Documentation: There are three important parts of Heapkeeper's documentation:
  the user documentation, the module documentation and the developer
  documentation. The user documentation consists of a single :doc:`tutorial`
  right now, with which we are satisfied and which is up-to-date. We plan to
  write a page about the customization of Heapkeeper, and also a cookbook. The
  module documentation mainly consists of the docstrings of classes and
  functions, which is written into the source code. This is complete and
  up-to-date (again, we don't count the issue tracker and the hkrcs). The
  developer documentation, which describes the ideas and main concepts of
  Heapkeeper at a higher level, is quite incomplete, but fortunately
  up-to-date.
- Homepage: The non-documentation part of the homepage is fine for now. We
  could improve the web page design by making a custom theme though.
- Workflow: our workflow has gone stable with the release of 0.3. We
  strongly rely on Git in continuous integration of bugfixes and new
  features into mature code.

28th January, 2010

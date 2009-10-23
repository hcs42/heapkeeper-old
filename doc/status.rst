Status
------

.. include:: defs.hrst

This page describes the status of the project's components.

- Source code: Heapkeeper is in a usable form now, although there are many
  things which could be done to make it more convenient. The source code is
  constantly in a good shape, all commits in the repository since May should
  work fine.
- Tests: we aim for 100% code coverage. We don't have that now, but we have
  3100 lines of test code for 6500 lines of normal code. All test pass in all
  commits since May.
- Documentation: There are three important parts of Heapkeeper's documentation:
  the user documentation, the module documentation and the developer
  documentation. The user documentation consists of a single :doc:`tutorial`
  right now, with which we are satisfied and which is up-to-date. We plan to
  write a page about the customization of Heapkeeper, and also a cookbook. The
  module documentation mainly consists of the docstrings of classes and
  functions, which is written into the source code. This is complete and
  up-to-date for |hkutils|, |hkshell| and |hkcustomlib|, but it is not ready
  for |hklib|, which is the largest module of all. The developer documentation,
  which describes the ideas and main concepts of Heapkeeper at a higher level,
  is also quite incomplete.
- Homepage: The non-documentation part of the homepage is fine for now. We
  could improve the web page design by making a custom theme though.
- Workflow: our workflow has gone stable with the release of 0.3. We
  strongly rely on Git in continuous integration of bugfixes and new
  features into mature code.

23th October, 2009

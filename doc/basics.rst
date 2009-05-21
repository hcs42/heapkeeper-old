Basics
======

The content of this page will be the following:

* Basic concepts: posts, post files.
* Basic hkshell

  * Basic commands:

    * general commands:

      * h()                - prints a detailed help
      * s()                - save
      * ga()               - generate all html

    * manipulating commands:

      * d(pps)             - delete
      * dr(pps)            - delete recursively
      * j(pp, pp)          - join two threads
      * e(pp)              - edit the post as a file
      * dl()               - download new mail

    * subject commands:

      * pS(pps)            - propagate subject
      * sS(pps, subj)      - set subject
      * sSr(pps, subj)     - set subject recursively

    * tag commands:

      * pt(pps)            - propagate tags
      * at(pps, pts)       - add tag/tags
      * atr(pps, pts)      - add tag/tags recursively
      * rt(pps, pts)       - remove tag/tags
      * rtr(pps, pts)      - remove tag/tags recursively
      * st(pps, pts)       - set tag/tags
      * str_(pps, pts)     - set tag/tags recursively

  * Features:

    * ``on`` and ``off`` commands

      * on(feature)        - turning a feature on
      * off(feature)       - turning a feature off

    * ``gen_indices``, ``gen_posts`` and ``save`` features

  * Intermediate hkshell:
    
    * running hkshell with parameters

    * commands that use :class:`hklib.Post`, :class:`hklib.PostDB` and
      :class:`hklib.PostSet` methods like:

      * :func:`hklib.PostSet.collect`
      * :func:`hklib.PostSet.forall`
      * :func:`hklib.PostDB.root`
      * :func:`hklib.PostDB.parent`
      * :func:`hklib.PostDB.children`
      * :func:`hklib.PostDB.set_subject`

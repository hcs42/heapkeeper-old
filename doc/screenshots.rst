Screenshots
===========

Using Heapkeeper's shell to download new posts and modify them:

.. image:: images/shell.png
      :align: center

.. .. Text in the screenshot:

.. .. $ python hk.py
.. .. Importing hkrc...
.. .. Importing hkrc OK
.. ..
.. .. >>> ls()  # listing all posts
.. .. <0> Powell in trouble  Peter Bogert  (2009.07.24. 11:36)
.. .. <1> Powell in trouble  Susan Calvin  (2009.07.24. 11:40)
.. .. >>> dl()  # downloading new posts
.. .. Reading settings...
.. .. Connecting...
.. .. Connected
.. .. Post #0 (#1 in INBOX) found.
.. .. Post #1 (#2 in INBOX) found.
.. .. Post #2 (#3 in INBOX) downloaded.
.. .. Downloading finished.
.. .. >>> ls()
.. .. <0> Powell in trouble  Peter Bogert  (2009.07.24. 11:36)
.. .. <1> Powell in trouble  Susan Calvin  (2009.07.24. 11:40)
.. .. <2> Powell in trouble  Peter Bogert  (2009.07.24. 11:58)
.. .. >>> cat(2)  # printing post 2
.. .. Heapid: 2
.. .. Author: Peter Bogert
.. .. Subject: Powell in trouble
.. .. Message-Id: <b29f917d080@mail.usrobots.com>
.. .. Date: Fri, 24 Jul 2009 11:58:24 +0000
.. ..
.. .. I have just found out, Donovan is also in trouble!
.. ..
.. .. Peter
.. .. >>> sSr(0, 'Powell and Donovan in trouble') # renaming the subject
.. .. >>> ls()
.. .. <0> Powell and Donovan in trouble  Peter Bogert  (2009.07.24. 11:36)
.. .. <1> Powell and Donovan in trouble  Susan Calvin  (2009.07.24. 11:40)
.. .. <2> Powell and Donovan in trouble  Peter Bogert  (2009.07.24. 11:58)

An index page of a heap:

.. image:: images/1.png
      :align: center

HTML page of a thread:

.. image:: images/2.png
      :align: center

If you like the screenshots, it may be a good idea to continue with the
:doc:`tutorial`, where you can find explanations and more screenshots.

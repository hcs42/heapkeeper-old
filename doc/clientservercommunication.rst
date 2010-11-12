Client and server communication in the web interface
====================================================

.. include:: defs.hrst

This page describes how the clients and servers communicate in Heapkeeper's web
interface (|hkweb|). The server is a Heapkeeper process (|hkshell|) executing a
web server thread (|hkweb|), while the client is a web browser executing the
JavaScript code received from the Heapkeeper server.

|hkweb| basically uses AJAX, but with JSON instead of XML. We can talk about
two kinds of messages: the queries sent from the client to the server, and the
responses sent from the server to the client. Both use JSON, but the former one
is a bit more complicated.

Queries sent from the client to the server
------------------------------------------

Queries are GET or POST requests. A GET or POST request has two parts that are
interesting for us now: the path and the query parameters. E.g. in the following
example::

    http://localhost:8080/my-server?key1=value1&key2=value2

``/my-server`` is the path and ``key1=value1&key2=value2`` is the string
representation of the list of query parameters.

In Heapkeeper, we want to be able to use such simple query parameters as shown
above (where all the keys and values are strings), but we also want to be able
to use any JSON object as a value. We solved this problem by making the binary
zero character special: if the value of a query parameter starts with a binary
zero, it means that it will be specified as a JSON object and not as a plain
string. Binary zero can be written as ``%00`` in query parameter list strings.
So all of these are legal query parameter list strings: ``key=value``,
``key=%00"value"`` (means exactly the same), ``key=%00[1,2]`` (means that the
value is a list of 1 and 2). The JSON objects have a standard stringified
format; that is used here.

If a client sends a GET or POST request, the class that serves it will be
determined by the path. The server class is usually a subclass of
:class:`hkweb.AjaxServer`. The class will be instantiated, and it starts by
converting the query parameter list string into a Python dictionary.

The following examples shows which Python dictionary is created from certain
query parameter list strings::

    Query: http://localhost:8080/my-server
    Python dictionary: {}

    Query: http://localhost:8080/my-server?key=value
    Python dictionary: {'key': 'value'}

    Query: http://localhost:8080/my-server?key1=value1&key2=value2
    Python dictionary: {'key1': 'value1', 'key2': 'value2'}

    Query: http://localhost:8080/my-server?key=%00"value"
    Python dictionary: {'key': 'value'}

    Query: http://localhost:8080/my-server?key=%00[1,2,3]
    Python dictionary: {'key': [1,2,3]}

    Query: http://localhost:8080/my-server?key1=%00{0:[1,2,3]},key2=other
    Python dictionary: {'key1': {0: [1,2,3]}, 'key2': 'other'}

The :func:`execute <hkweb.AjaxServer.execute>` method of the server object will
be called with this Python dictionary as the ``args`` argument. The server
object itself will decide which keys to read and which objects to expect there.
The expected dictionary format is specified in the docstring of the ``execute``
method of the server.

Responses sent from the server to the client
--------------------------------------------

The response is more simple: it is always the stringified format of a JSON
object. It is usually a dictionary. Its fields depend on the concrete server
and are specified in the docstring of the ``execute`` method of the server.
There is no binary zero here, because we always send a JSON object, so there is
no need to distinguish between them and the plain strings.

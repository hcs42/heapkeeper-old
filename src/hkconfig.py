# This file is part of Heapkeeper.
#
# Heapkeeper is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# Heapkeeper is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# Heapkeeper.  If not, see <http://www.gnu.org/licenses/>.

# Copyright (C) 2010 Csaba Hoch
# Copyright (C) 2010 Attila Nagy

"""|hkconfig| reads the Heapkeeper configuration files and converts them into
dictionaries."""


import hkutils


def unify_config(config):
    """Modifies the configuration object to conform to a unified format.

    The `config` object has the following format::

        {'heaps': {HeapName: {'path': str,
                              ['id': str,]
                              ['name': str,]
                              [Server,]
                              ['nicknames': Nicknames]}},
         ['paths': {['html_dir': str]}],
         [Server,]
         ['nicknames': Nicknames],
         ['accounts': Accounts]}

        Nicknames:

            {EmailAddress: str(nickname)}

        Accounts:

            {str(username): str(password)}

        Server:

            'server': {'host': str,
                       'port': str(int),
                       'username': str,
                       ['password': str]}

    Unified format::

        {'paths': {'html_dir': (str | None)},
         'heaps': {HeapName: {'path': str,
                              'id': str,
                              'name': str,
                              [Server,]
                              'nicknames': Nicknames}},
         [Server,]
         'nicknames': Nicknames,
         'accounts': Accounts},

        Server:

            {'server': {'host': str,
                        'port': int,
                        'username': str,
                        ['password': str]}}

    Definitions (in BNF):

    - HeapSequence (str) ::= ``"<heapid>:<heap>{;<heapid>:<heap>}"``
    - Nickname (str) ::= ``"<nickname><space><email address>"``
    - HeapName (str)

    **Argument:**

    - `config` (|ConfigDict|)

    **Returns:** |ConfigDict|
    """

    path = config.get('paths', [])
    if 'heaps' in path:
        raise hkutils.HkException(
            'This config file format ("format 2") cannot be used any more.')
    elif 'mail' in path:
        raise hkutils.HkException(
            'This config file format ("format 1") cannot be used any more.')
    else:
        return unify_format_3(config)

def unify_str_to_str_dict(dictionary):
    """Checks if a dict assigns strings to strings.

    In format 3, both the `nicknames` and the `accounts` dict is of
    this form.

    **Argument:**

    - `dictionary` ({str: str})
    """

    for key, value in dictionary.items():
        assert isinstance(key, str)
        assert isinstance(value, str)

def unify_server(server):
    """Converts the `server` dictionary given in format 3 to the unified
    format.

    **Argument:**

    - `server` ({str: str})
    """

    if server is not None:
        assert isinstance(server['host'], str)
        assert isinstance(server['port'], str)
        server['port'] = int(server['port'])
        assert isinstance(server['username'], str)
        assert isinstance(server.get('password', ''), str)

def unify_format_3(config):
    """Converts the configuration object in format 3 into the unified
    configuration format.

    The `config` parameter is modified and returned.

    **Argument:**

    - `config` (|ConfigDict|)

    **Returns:** |ConfigDict|
    """

    # paths/html_dir
    config.setdefault('paths', {})
    config['paths'].setdefault('html_dir', None)

    # heaps/<heap name>
    for heap_name, heap_dict in config['heaps'].items():
        assert isinstance(heap_dict['path'], str)
        heap_dict.setdefault('id', heap_name)
        heap_dict.setdefault('name', heap_name)

        # heaps/<heap name>/server
        unify_server(heap_dict.get('server'))

        # heaps/<heap name>/nicknames
        heap_dict.setdefault('nicknames', {})
        unify_str_to_str_dict(heap_dict['nicknames'])

    # server
    unify_server(config.get('server'))

    # nicknames
    config.setdefault('nicknames', {})
    unify_str_to_str_dict(config['nicknames'])

    # accounts
    config.setdefault('accounts', {})
    unify_str_to_str_dict(config['accounts'])

    return config

// This file is part of Heapkeeper.
//
// Heapkeeper is free software: you can redistribute it and/or modify it
// under the terms of the GNU General Public License as published by the Free
// Software Foundation, either version 3 of the License, or (at your option) any
// later version.
//
// Heapkeeper is distributed in the hope that it will be useful, but
// WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
// FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
// more details.
//
// You should have received a copy of the GNU General Public License along with
// Heapkeeper.  If not, see <http://www.gnu.org/licenses/>.

// Copyright (C) 2010 Csaba Hoch

function assertEqual(actual, expected) {
    if (actual != expected) {
        hk_unittest_result +=
            'Test fail: the following values are not equal:\n' +
            'Actual:\n' +
            actual + '\n' +
            'Expected:\n' +
            expected + '\n\n';
    }
}

function test_PostIdStr() {
    assertEqual(postIdToPostIdStr('my_heap-1'), 'my_heap/1');
    assertEqual(postIdStrToPostId('my_heap/1'), 'my_heap-1');
}

function test_url_and_dict_to_http_query() {

    // Test template:
    //
    // test(
    //     <url>, <args>,
    //     <escaped result>,
    //     <unescaped result>)

    function test_core(url, args, expected_escaped, expected_unescaped) {
        actual_result = url_and_dict_to_http_query(url, args),
        assertEqual(actual_result, expected_escaped);
        assertEqual(unescape(actual_result), expected_unescaped);
    }

    // Basic test
    test_core(
        'myurl', {'key': 'value'},
        'myurl?key=%00%22value%22',
        'myurl?key=\x00"value"');

    // Empty test
    test_core(
        'myurl', {},
        'myurl',
        'myurl');

    // Testing multiple key-value pairs
    test_core(
        'myurl', {'key1': 'value1', 'key2': 'value2'},
        'myurl?key1=%00%22value1%22&key2=%00%22value2%22',
        'myurl?key1=\x00"value1"&key2=\x00"value2"');

    // Testing a list as a value
    test_core(
        'myurl', {'key': [1, 1.0, true]},
        'myurl?key=%00%5B1%2C1%2Ctrue%5D',
        'myurl?key=\x00[1,1,true]');

    // Testing a dictionary as a value
    test_core(
        'myurl', {'key': {'key2': 42}},
        'myurl?key=%00%7B%22key2%22%3A42%7D',
        'myurl?key=\x00{"key2":42}');
}

var hk_unittest_result = '';

function do_test() {
    // Executes the unit tests.

    test_PostIdStr();
    test_url_and_dict_to_http_query();

    if (hk_unittest_result == '') {
        hk_unittest_result = 'All tests passed.';
    }

    $('#result').text('Test result:\n\n' + hk_unittest_result);
}

$(document).ready(function() {
    do_test();
});


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

var hk_unittest_result = '';

function do_test() {
    // Executes the unit tests.

    test_PostIdStr();

    if (hk_unittest_result == '') {
        hk_unittest_result = 'All tests passed.';
    }

    $('#result').text('Test result:\n\n' + hk_unittest_result);
}

$(document).ready(function() {
    do_test();
});


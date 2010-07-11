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


function search() {
    // Loads the search page with the contents of the #searchbar-term input
    // text as the search term.
    gotoURL('', {'term': $('#searchbar-term').val()});
}

$(document).ready(function() {
    $('#searchbar-container-form').bind('submit', function() {
        search();
        return false; // don't execute the normal "submit"
    });
});

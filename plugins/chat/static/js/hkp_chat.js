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

// Copyright (C) 2010 Attila Nagy

$('#chattextinput').keypress(function(event) {
    if (event.keyCode == '13')
        sendMsg();
});

function sendMsg() {
    var text = $('#chattextinput');
    var msg = text.val();
    $.post('/chat-send', {'l': msg});
    text.val('');
}

function getMsg() {
    $.ajax({
        url: '/chat-poll/' + session,
        dataType: 'text',
        type: 'get',
        success: function(line) {
            var chatmsg = $('#chatmessages');
            chatmsg.append(line);
            chatmsg.scrollTop(chatmsg.attr('scrollHeight'));
            setTimeout('getMsg()', 1000);
            }
    });
}

session = Math.floor(Math.random()*1000000);

getMsg();

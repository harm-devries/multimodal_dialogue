$(document).ready(function(){
    namespace = '/test';
    var $window = $(window);
    var socket = io.connect('https://' + document.domain + ':' + location.port + namespace);
    var username;

    socket.on('disconnect', function() {
        $('.log').append('<br>Disconnected');
    });
    socket.on('usercount', function(msg) {
        $('#active_users').text(msg.num_users + ' active users');
    });
    socket.on('no partner', function(msg) {
        $('#title').hide();
        $('#intro').html('<div class="well"><span class="loader"><span class="loader-inner"></span></span> Waiting for a new partner...</div>');
    })
    socket.on('questioner', function(msg) {
        $('#intro').hide();
        $('#waiting_text').text('Waiting for an answer');
        setImage(msg.data);
        $('#question').show()
        $('#guess').show();
    })
    socket.on('answerer', function(msg) {
        $('#intro').hide();
        setImage(msg.data);
        $('#waiting_text').text('Waiting for a new question');
        $('#waiting').show();
    })
    socket.on('newquestion', function(msg) {
        addQuestion(msg);
        $('#waiting').hide();
        $('#answer').fadeIn(1000);
    });
    socket.on('new answer', function(msg) {
        addAnswer(msg);
        $('#waiting').hide();
        $('#question').fadeIn(1000);
    });

    function addAnswer(msg){
        $('.log').prepend('<div class="row"><div class="col-sm-1"><h3>A:</h3></div><div class="well well-sm col-sm-11">' + msg + '</div></div>');
    }
    function addQuestion(msg){
        $('.log').prepend('<div class="row"><div class="col-sm-1"><h3>Q:</h3></div><div class="well well-sm col-sm-11">' + msg + '</div></div>');
    }

    function setImage(img) {
        $('#title').hide();
        $('.log').show();
        $('#image').show();
        $('#image').html(img);
    }
    // Sets the client's username
    function setUsername () {
        username = cleanInput($usernameInput.val().trim());

        // If the username is valid
        if (username) {
            $loginPage.hide();
            $chatPage.show();
            $loginPage.off('click');
            $('#welcome').show()
            $('#welcome').text('Welcome ' + username)
            // Tell the server your username
            socket.emit('add user', username);
        }
    }

    // Prevents input from having injected markup
    function cleanInput (input) {
        return $('<div/>').text(input).text();
    }

    // event handler for server sent data
    // the data is displayed in the "Received" section of the page
    // handlers for the different forms in the page
    // these send data to the server in a variety of ways


    $('a#newgame').click(function(event) {
        $('#p_newgame').hide();
        socket.emit('next');
        return false;
    });
    $('a#ask').click(function(event) {
        $('#question').hide();
        $('#waiting').fadeIn(1000);
        var msg = $('#newquestion').val();
        $('#newquestion').val('');
        addQuestion(msg);
        socket.emit('newquestion', msg);
        return false;
    });
    $('a#yes').click(function(event) {
        addAnswer('Yes');
        $('#answer').hide();
        $('#waiting').fadeIn(1000);
        socket.emit('new answer', 'Yes');
        return false;
    });
    $('a#no').click(function(event) {
        addAnswer('No');
        $('#answer').hide();
        $('#waiting').fadeIn(1000);
        socket.emit('new answer', 'No');
        return false;
    });
    $('a#na').click(function(event) {
        addAnswer('Not applicable');
        $('#answer').hide();
        $('#waiting').fadeIn(1000);
        socket.emit('new answer', 'Not applicable');
        return false;
    });


    $window.keydown(function (event) {
        // Auto-focus the current input when a key is typed
        if (!(event.ctrlKey || event.metaKey || event.altKey)) {
            $currentInput.focus();
        }
        // When the client hits ENTER on their keyboard
        if (event.which === 13) {
            if (username) {
                $('#question').hide()
                var message = $('#questionInput').val()
                $('#log').append('<div class="alignleft">' + message + '</div><br/>')
                socket.emit('new question', message)
            } else {
                setUsername();
            }
        }
    });
});
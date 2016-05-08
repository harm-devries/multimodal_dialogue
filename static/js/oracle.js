$(document).ready(function() {
    namespace = '/oracle';
    var socket = io.connect('https://' + document.domain + ':' + location.port + namespace);
    var img; //image url
    var object; // selected object for oracle
    var correct_obj; // if flag is true, segment will be displayed in green
    var show_obj = true; // if true, segment will be displayed
    var scale;
    var img_canvas = $('canvas#img')[0];
    var img_ctx = img_canvas.getContext("2d");
    var segment_canvas = $('canvas#segment')[0];
    var segment_ctx = segment_canvas.getContext("2d");
    var partner_disconnect = false;
    var partner_timeout = false;
    var colors = [[255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 0], [255, 0, 255], 
                  [255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 0], [255, 0, 255], 
                  [255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 0], [255, 0, 255],
                  [255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 0], [255, 0, 255],
                  [255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 0], [255, 0, 255],
                  [255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 0], [255, 0, 255]];
    var fadeS = 600;
    var round = 0;
    var score = 0;

    var time = 0;
    var timer_id;
    var answer_time = 30;
    var question_time = 90;
    var guess_time = 30;

    // socket.on('disconnect', function() {
    //     $('#question').hide();
    //     $('#answer').hide();
    //     $('#waiting').hide();
    //     $('#info_text').text('Sorry! The server unexpectedly closed the connection. ');
    //     $('#info_text').show();
    // });
    socket.on('partner_disconnect', function() {
        partner_disconnect = true;
        deletegame();
        noPartner();
    });
    socket.on('partner timeout', function() {
        partner_timeout = true;
        deletegame();
        noPartner();
    });

    socket.on('answerer', function(msg) {
        setTimeout(function(){
            $('#info_text').html('<span class="loader"><span class="loader-inner"></span></span> We have found a partner!');
        }, 1000);

        setTimeout(function(){
            $('#title').fadeOut(fadeS);
            $('#intro').fadeOut(fadeS);
            $('#info_text').hide();
            img = msg.img;
            object = msg.object;
            correct_obj = true;
            show_obj = true;
            $('#image').show();

            renderImageAndSegment();
            $('#waiting_text').text('Waiting for a new question');
            wait_for_question();
            set_object();
            $('#score').fadeIn(fadeS);
        }, 2000);
    })
    socket.on('new question', function(msg) {
        addQuestion(msg);
        show_answer_form();
    });
    socket.on('all annotations', function(msg) {
        wait_for_guess();
    });
    socket.on('correct annotation', function(msg) {
        objs = null;
        object = null;
        clearInterval(timer_id);
        clearCanvas(segment_ctx, segment_canvas);
        $('#log').hide();
        $('#object').hide();
        $('#waiting').hide();

        $('#info').switchClass('default', 'success', 100);
        text = '<i class="fa fa-check-circle fa-2x"></i> <h3 style="margin-left: 10px; display: inline">Correct!</h3>';
        
        // set object
        correct_obj = true;
        show_obj = true;
        object = msg.object;
        set_object();
        renderSegment(object.segment, scale, segment_ctx);

        $('#newgame_text').html('<h3 style="margin-bottom:20px">In a winning mood?</h3>');
        $('#info_text').html(text); 
        $('#info_text').fadeIn(fadeS);
        $('#p_newgame').show();
        deletegame();
        score += 10;
        set_score();
    });

    socket.on('wrong annotation', function(msg) {
        objs = null;
        object = null;
        clearInterval(timer_id);
        clearCanvas(segment_ctx, segment_canvas);
        $('#log').hide();
        $('#waiting').hide();

        // set message
        $('#info').switchClass('default', 'error', 100);
        correct_obj = false;
        text = '<i class="fa fa-times-circle fa-2x"></i> <h3 style="margin-left: 10px; display:inline">Incorrect!</h3> <span style="float: right; line-height: 35px;">Your partner guessed:</span>';

        // set object
        show_obj = true;
        object = msg.object;
        set_object();
        renderSegment(object.segment, scale, segment_ctx);

        $('#info_text').html(text); 
        $('#info_text').fadeIn(fadeS);
        $('#newgame_text').html('<h3 style="margin-bottom:20px">Try it one more time?</h3>');
        $('#p_newgame').show();
        $('#p_newplayergame').show();
    });

    function wait_for_question() {
        $('#answer').hide();
        $('#waiting').show();
        time = question_time;
        clearInterval(timer_id);
        set_time('#w_time');
        timer_id = setInterval(set_time.bind(null, '#w_time'), 1000);
    }

    function wait_for_guess() {
        $('#answer').hide();
        $('#waiting_text').text('Your partner started guessing..');
        $('#waiting').show();
        time = guess_time;
        clearInterval(timer_id);
        set_time('#w_time');
        timer_id = setInterval(set_time.bind(null, '#w_time'), 1000);
    }

    function show_answer_form() {
        $('#waiting').hide();
        $('#answer').fadeIn(1000);
        time = answer_time;
        clearInterval(timer_id);
        set_time('#a_time');
        timer_id = setInterval(set_time.bind(null, '#a_time'), 1000);
    }

    function set_time(time_id) {
        if (time > 0) {
            time -= 1;
        }
        $(time_id).text(time);
        if (time == 0 && time_id != "#w_time") {
            socket.emit('timeout');
            clearInterval(timer_id);
            setTimeout(function(){
                window.location = '/oracle';
            }, 1000);
        }
    }

    function set_object() {
        $('#segment_canvas').unbind('mouseenter mouseleave');
        $('#object').html('<img width="34px" height="34px" src="http://mscoco.org/static/icons/' + object.category_id + '.jpg" /> ' + object.category);
        var link = $('<a style="margin-left: 20px" href="#">Hide</a>').click(function(event) {
            if($(this).text() == 'Hide') {
                $(this).text('Show');
                show_obj = false;
                clearCanvas(segment_ctx, segment_canvas);
            } else {
                $(this).text('Hide');
                show_obj = true;
                renderSegment(object.segment, scale, segment_ctx, correct_obj);
            }
        })
        $('#object').append(link);
        $('#object').fadeIn(fadeS);
    }

    function set_score() {
        $('#score').html('Your score: <h3 style="display:inline; margin: 0">'+score+'</h3>');
    }

    function deletegame() {
        object = null;
        objs = null;
        round = 0;
        $('#log').html('');
        $('#log').show();
        clearCanvas(segment_ctx, segment_canvas);
    }

    function hideAll() {
        $('#intro').hide();
        $('#answer').hide();
        $('#question').hide();
        $('#waiting').hide();
        $('#guess').hide();
        $('#image').hide();
        $('#object').hide();
        $('#info_text').hide();
    }

    function noPartner() {
        hideAll();
        $('#title').fadeOut(fadeS);
        $('#intro').fadeOut(fadeS);
        $('#p_newgame').fadeOut(fadeS);
        $('#p_newplayergame').fadeOut(fadeS);
        var msg;
        if(partner_disconnect) {
            msg = 'Your partner disconnected. Searching for a new one..';
            partner_disconnect = false;
        } else if (partner_timeout) {
            msg = 'Your partner timed out. Searching for a new one..';
            partner_timeout = false;
        } else {
            msg = 'Searching for a partner..';
        }
        $('#info_text').html('<span class="loader"><span class="loader-inner"></span></span> ' + msg);
        $('#info_text').show();
        infoBarDown();
    }

    function infoBarDown() {
        $('body').animate({
            paddingTop: "110px"
        }, 1000);
        $('#info').animate({
            height: "55px",
            paddingTop: "10px",
            paddingBottom: "10px"
        }, 1000);
        $('#left').switchClass("col-sm-6", "col-sm-5", 0, "easeInOutQuad");
        $('#right').switchClass("col-sm-6", "col-sm-7", 0, "easeInOutQuad");

    }
    function infoBarUp() {
        $('body').animate({
            paddingTop: "60px"
        }, 1000);
        $('#info').animate({
            height: "0px",
            padding: "0px"
        }, 1000);
        // $('#left').switchClass("col-sm-5", "col-sm-9", 0, "easeInOutQuad");
        // $('#right').switchClass("col-sm-7", "col-sm-3", 0, "easeInOutQuad");
    }

    function addAnswer(msg){
        if (msg == 'Yes') {
            msg = '<span style="color: #61b832">Yes</span>';
        } else if (msg == 'No') {
            msg = '<span style="color: #de4343">No</span>';
        } else {
            msg = '<span style="color: #4ea5cd">Not applicable</span>';
        }
        if (round % 2 == 0) {
            $('#q'+round).after('<div class="well well-sm">' + msg + '</div>');
        } else {
            $('#q'+round).after('<div class="well well-sm" style="background-color: #fff;">' + msg + '</div>');
        }
        scrollBottom();
        round += 1;
    }
    function addQuestion(msg){
        if (round % 2 == 0) {
            $('#log').prepend('<div id="q'+round+'" class="well well-sm" style="margin-top: 10px;">' + msg + '</div>');
        } else {
            $('#log').prepend('<div id="q'+round+'" class="well well-sm" style="background-color: #fff;margin-top: 10px;">' + msg + '</div>');
        }
        scrollBottom();
    }

    // event handler for server sent data
    // the data is displayed in the "Received" section of the page
    // handlers for the different forms in the page
    // these send data to the server in a variety of ways
    $('a#newgame').click(function(event) {
        deletegame();
        $('#info').switchClass('success', 'default', 0);
        $('#info').switchClass('error', 'default', 0);
        $('#name_div').hide();
        noPartner();
        socket.emit('next questioner');
        return false;
    });  
    $('a#yes').click(function(event) {
        wait_for_question();
        msg = 'Yes';
        addAnswer(msg);
        socket.emit('new answer', msg);
        return false;
    });
    $('a#no').click(function(event) {
        wait_for_question();
        msg = 'No';
        addAnswer(msg);
        
        socket.emit('new answer', msg);
        return false;
    });
    $('a#na').click(function(event) {
        wait_for_question();
        msg = 'N/A';
        addAnswer(msg);
        socket.emit('new answer', msg);
        return false;
    });

    function renderImageAndSegment() {
        scale = get_scale($('#image').width(), img.width, $('.center-container').height() - 30, img.height);
        var new_width = parseInt(img.width*scale);
        var new_height = parseInt(img.height*scale);
        set_canvas_size(img_canvas, new_width, new_height);
        renderImage(img_canvas, img_ctx, img.src, new_width, new_height);
        set_canvas_size(segment_canvas, new_width, new_height);
        renderSegment(object.segment, scale, segment_ctx, correct_obj);
    }

    $(window).resize(function() {
        renderImageAndSegment();
        resizeLog();
    });
});

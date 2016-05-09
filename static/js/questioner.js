$(document).ready(function() {
    namespace = '/questioner1';
    var socket = io.connect('http://' + document.domain + ':' + location.port + namespace);
    var img; //image url
    var object; // selected object for oracle
    var correct_obj; // if flag is true, segment will be displayed in green
    var show_obj = true; // if true, segment will be displayed
    var scale; // scale of image compared to original size
    var img_canvas = $('canvas#img')[0];
    var img_ctx = img_canvas.getContext("2d");
    var segment_canvas = $('canvas#segment')[0];
    var segment_ctx = segment_canvas.getContext("2d");
    var objs; // All annotations. Only defined after questioner pressed guess button
    var partner_disconnect = false;
    var partner_timeout = false;
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

    socket.on('questioner', function(msg) {
        console.log('questioner');
        setTimeout(function(){
            $('#info_text').html('<span class="loader"><span class="loader-inner"></span></span> We have found a partner!');
        }, 1000);
        
        setTimeout(function(){
            $('#title').fadeOut(fadeS);
            $('#intro').fadeOut(fadeS);
            $('#info_text').hide();
            $('#waiting_text').text('Waiting for an answer..');
            $('#waiting').hide();
            $('#image').show();
            img = msg.img;
            renderImageAndSegment();
            show_question_form();
            $('#report').fadeIn(fadeS);
        }, 2000);
    });
    socket.on('new answer', function(msg) {
        addAnswer(msg);
        show_question_form();
    });
    socket.on('all annotations', function(msg) {
        $('#question').hide();
        $('#guess').hide();
        $('#object').html('<span id="g_time" style="margin-right: 20px"></span><b>Please click on one of the objects.</b>');
        $('#object').show();
        time = guess_time;
        clearInterval(timer_id);
        set_time('#g_time');
        timer_id = setInterval(set_time.bind(null, '#g_time'), 1000);
        objs = msg.objs;
        renderSegments(objs, scale, segment_ctx);
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

        $('#info_text').html(text); 
        $('#info_text').fadeIn(fadeS);
        $('#mturk_form').show();
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
        text = '<i class="fa fa-times-circle fa-2x"></i> <h3 style="margin-left: 10px; display:inline">Incorrect!</h3> <span style="float: right; line-height: 35px;">The correct object was:</span>';
        correct_obj = true;

        // set object
        show_obj = true;
        object = msg.object;
        set_object();
        renderSegment(object.segment, scale, segment_ctx, correct_obj);

        $('#info_text').html(text); 
        $('#info_text').fadeIn(fadeS);
        $('#newgame_text').html('<h3 style="margin-bottom:20px">Try it one more time?</h3>');
        $('#p_newgame').show();
        deletegame();
    });

    function wait_for_answer() {
        $('#question').hide();
        $('#waiting').show();
        $('#newquestion').val('');
        time = answer_time;
        clearInterval(timer_id);
        set_time('#w_time');
        timer_id = setInterval(set_time.bind(null, '#w_time'), 1000);
    }


    function show_question_form() {
        $('#waiting').hide();
        $('#question').fadeIn(1000);
        $('#guess').show();
        $('#newquestion').focus();
        time = question_time;
        clearInterval(timer_id);
        set_time('#q_time');
        timer_id = setInterval(set_time.bind(null, '#q_time'), 1000);
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
                window.location.reload(false);
            }, 1000);
        }
    }

    function set_object() {
        $('#segment_canvas').unbind('mouseenter mouseleave');
        $('#object').html('<img width="34px" height="34px" src="http://mscoco.org/static/icons/' + object.category_id + '.jpg" /> ' + object.category);
        var link = $('<a style="margin-left: 20px" href="#">Hide mask</a>').click(function(event) {
            if($(this).text() == 'Hide mask') {
                $(this).text('Show mask');
                show_obj = false;
                clearCanvas(segment_ctx, segment_canvas);
            } else {
                $(this).text('Hide mask');
                show_obj = true;
                renderSegment(object.segment, scale, segment_ctx);
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
        $('#report').hide();
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
    $('a#guessbtn').click(function(event) {
        $('#guessbtn').attr('disabled', false); 
        socket.emit('guess');
        return false;
    });
    $('a#newgame').click(function(event) {
        deletegame();
        $('#info').switchClass('success', 'default', 0);
        $('#info').switchClass('error', 'default', 0);
        $('#name_div').hide();
        noPartner();
        socket.emit('next oracle');
        return false;
    });
    $('a#ask').click(function(event) {
        var msg = $('#newquestion').val();
        if (msg == '' || msg.match(/\S+/g).length < 3) {
            alert('Please use at least 3 words for a question.');
        } else {
            wait_for_answer();
            addQuestion(msg);
            socket.emit('newquestion', msg);
        }
        return false;
    });
    $("#newquestion").keyup(function(event){
        if(event.keyCode == 13){
            $("a#ask").click();
        }
    });
    $('canvas#segment').mousemove(function (e) {
        if(objs != null) {
            arr = getMousePosition(e);
            var mouseX = arr[0], mouseY = arr[1];
            clearCanvas(segment_ctx, segment_canvas);
            renderSegments(objs, scale, segment_ctx, mouseX, mouseY);
        }
    });
    segment_canvas.addEventListener('click', function(e) {
        if(objs != null) {
            arr = getMousePosition(e);
            var mouseX = arr[0], mouseY = arr[1];
            var id = getObjectFromClick(mouseX, mouseY, objs, scale);
            if (id != undefined) {
                $('canvas#segment').css('cursor', 'default');
                socket.emit('guess annotation', id);
            }
        }
    }, false);

    function renderImageAndSegment() {
        if (img != undefined) {
            scale = get_scale($('#image').width(), img.width, $('.center-container').height() - 30, img.height);
            var new_width = parseInt(img.width*scale);
            var new_height = parseInt(img.height*scale);
            set_canvas_size(img_canvas, new_width, new_height);
            renderImage(img_canvas, img_ctx, img.src, new_width, new_height);
            set_canvas_size(segment_canvas, new_width, new_height);
            if (objs != null) {
                renderSegments(objs, scale, segment_ctx);
            }
        }
    }

    $(window).resize(function() {
        renderImageAndSegment();
        resizeLog();
    });
});

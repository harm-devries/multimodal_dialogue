$(document).ready(function() {
    namespace = $('#namespace').data().name;
    var socket = io.connect('https://' + document.domain + ':' + location.port + namespace, {rememberTransport: false});
    /* parse url params and send assignmentId, hitId and workerId to server */
    var QueryString = function () {
          // This function is anonymous, is executed immediately and 
          // the return value is assigned to QueryString!
          var query_string = {};
          var query = window.location.search.substring(1);
          var vars = query.split("&");
          for (var i=0;i<vars.length;i++) {
            var pair = vars[i].split("=");
                // If first entry with this name
            if (typeof query_string[pair[0]] === "undefined") {
              query_string[pair[0]] = decodeURIComponent(pair[1]);
                // If second entry with this name
            } else if (typeof query_string[pair[0]] === "string") {
              var arr = [ query_string[pair[0]],decodeURIComponent(pair[1]) ];
              query_string[pair[0]] = arr;
                // If third or later entry with this name
            } else {
              query_string[pair[0]].push(decodeURIComponent(pair[1]));
            }
          } 
          return query_string;
    }();
    socket.emit('update session', {assignmentId: QueryString.assignmentId,
                                   hitId: QueryString.hitId,
                                   workerId: QueryString.workerId});

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
    vex.defaultOptions.className = 'vex-theme-default';


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
    socket.on('reported', function(){
        deletegame();
        noPartner();
        vex.dialog.alert({
            message: 'Your partner has reported your playing behavior. We will start a new game, but please play appropriately to avoid further consequences.',
        });
    });

    socket.on('questioner', function(msg) {
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
    socket.on('update answer', function(msg){
        updateAnswer(msg.round, msg.old_msg, msg.new_msg);
        vex.dialog.alert({
            message: 'Your partner changed his answer to the question "'+ $('#q'+msg.round).text() +'" from '+msg.old_msg+' to '+msg.new_msg+'.',
            callback: function(value) {
                setTimeout(function(){
                    $('#newquestion').focus();
                }, 500);
            }
        });
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
        deletegame();
        clearInterval(timer_id);
        $('#log').hide();
        $('#waiting').hide();

        $('#info').switchClass('default', 'success', 100);

        text = '<i class="fa fa-check-circle fa-2x"></i> <h3 style="margin-left: 10px; display: inline">Correct!</h3>';
        // set object
        correct_obj = true;
        show_obj = true;
        object = msg.object;
        set_object();
        renderSegment(object.segment, scale, segment_ctx, correct_obj);

        $('#info_text').html(text); 
        $('#info_text').fadeIn(fadeS);

         if (msg.finished) {
            $('#qualified').show();
        } else {
            $('#newgame_text').html('<p style="margin-bottom: 20px">You have to finish ' + (10 - msg.stats.success) + ' more games to complete the HIT. </p>');
            $('#p_newgame').show();
        }
        set_score(msg.stats.success, msg.stats.failure, msg.stats.questioner_disconnect + msg.stats.questioner_timeout);
    });
    socket.on('wrong annotation', function(msg) {
        deletegame();
        clearInterval(timer_id);
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
        if (msg.finished) {
            $('#newgame_text').html('<p style="margin-bottom: 20px">You have are successfully qualified. </p>');
        } else {
            $('#newgame_text').html('<p style="margin-bottom: 20px">You have to finish ' + (10 - msg.stats.success) + ' more games to complete the HIT. </p>');
        }
        $('#p_newgame').show();
        set_score(msg.stats.success, msg.stats.failure, msg.stats.questioner_disconnect + msg.stats.questioner_timeout);
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
                renderSegment(object.segment, scale, segment_ctx, correct_obj);
            }
        })
        $('#object').append(link);
        $('#object').fadeIn(fadeS);
    }

    function set_score(success, failure, disconnect) {
        $('#nr_successes').html(success);
        $('#nr_failures').html(failure);
        $('#nr_disconnects').html(disconnect);
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
        $('#instructions').fadeOut(fadeS);
        $('#p_newgame').fadeOut(fadeS);
        $('#p_newplayergame').fadeOut(fadeS);
        var msg;
        if(partner_disconnect) {
            msg = 'Your partner disconnected. Waiting for a new one..';
            partner_disconnect = false;
        } else if (partner_timeout) {
            msg = 'Your partner timed out. Waiting for a new one..';
            partner_timeout = false;
        } else {
            msg = 'Waiting for a partner..';
        }
        $('#info_text').html('<span class="loader"><span class="loader-inner"></span></span> ' + msg);
        $('#info_text').show();
        infoBarDown();
        // setTimeout(function(){
        //     $('#intro').show();
        //     $('#intro').html('We couldn\'t find a partner for you at the moment. Please come back later. <br /><br /> (You could also try to refresh the webpage - sometimes sockets fail to connect to the webserver.).')
        // }, 30000);
    }

    function infoBarDown() {
        $('body').animate({
            paddingTop: "115px"
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

    function colorizeAnswer(msg, line_through) {
        if (msg == 'Yes') {
            if (!line_through) {
                msg = '<span style="color: #61b832;">Yes</span>';
            } else {
                msg = '<span class="strike" style="color: #61b832">Yes</span>';
            }
        } else if (msg == 'No') {
            if (!line_through) {
                msg = '<span style="color: #de4343">No</span>';
            } else {
                msg = '<span class="strike" style="color: #de4343;">No</span>';
            }
        } else {
            if (!line_through) {
                msg = '<span style="color: #4ea5cd">Not applicable</span>';
            } else {
                msg = '<span class="strike" style="color: #4ea5cd;">Not applicable</span>';
            }
        }
        return msg;
    }

    function updateAnswer(r, old_msg, new_msg) {
        old_msg_html = colorizeAnswer(old_msg, true);
        new_msg_html = colorizeAnswer(new_msg);
        $('#a'+r).html(old_msg_html + '&nbsp; &nbsp;' + new_msg_html);
    }

    function addAnswer(msg){
        col_msg = colorizeAnswer(msg);
        if (round % 2 == 0) {
            $('#q'+round).after('<div id="a'+round+'" class="well well-sm" style="font-weight: 500">' + col_msg + '</div>');
        } else {
            $('#q'+round).after('<div id="a'+round+'" class="well well-sm" style="background-color: #fff; font-weight: 500">' + col_msg + '</div>');
        }
        scrollBottom();
        round += 1;
    }
    function addQuestion(msg){
        if (round % 2 == 0) {
            $('#log').prepend('<div id="q'+round+'" class="well well-sm" style="font-weight: 500">' + msg + '</div>');
        } else {
            $('#log').prepend('<div id="q'+round+'" class="well well-sm" style="background-color: #fff; font-weight: 500">' + msg + '</div>');
        }
        if (round > 0) {
            $('#q'+(round - 1)).css('margin-top', '10px');
        }
        scrollBottom();
    }

    // event handler for server sent data
    // the data is displayed in the "Received" section of the page
    // handlers for the different forms in the page
    // these send data to the server in a variety of ways

    $('a#report_user').click(function(event) {
        vex.dialog.prompt({
          message: 'This will end the game. ',             // adds the content message
          placeholder: 'Please specify a reason',      // text displayed in Prompt input field

          // calls a callback function, with simple Alert message
          // if the user adds data in the input field, "value" contains that text, if Cancel, value is false,
          // if OK with no data added in input field, value is an object with empty "vex" property
          callback: function(value) {
            if(value !== false && value != '') {
                deletegame(); 
                noPartner(); 
                socket.emit('report oracle', value);
            } 
          }
        });
    });
    $('a#guessbtn').click(function(event) {
        if (round > 0) {
            $('#guessbtn').attr('disabled', false); 
            socket.emit('guess');
            return false;
        } else {
            vex.dialog.alert({
            message: 'You have to ask at least one question before you can guess the object.',
            callback: function(value) {
                    setTimeout(function(){
                        $('#newquestion').focus();
                    }, 500);
                }
            });
        }
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
            vex.dialog.alert({
                message: 'Please use at least 3 words for a question.',
                callback: function(value) {
                    setTimeout(function(){
                        $('#newquestion').focus();
                    }, 500);
                }
            });
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
            scale = get_scale($('#image').width(), img.width, $('.center-container').height() - 15, img.height);
            var new_width = parseInt(img.width*scale);
            var new_height = parseInt(img.height*scale);
            set_canvas_size(img_canvas, new_width, new_height);
            renderImage(img_canvas, img_ctx, img.src, new_width, new_height);
            set_canvas_size(segment_canvas, new_width, new_height);
            if (object != null) {
                renderSegment(object.segment, scale, segment_ctx, correct_obj);
            }
            if (objs != null) {
                renderSegments(objs, scale, segment_ctx);
            }
        }
    }

    $(window).resize(function() {
        if(img != undefined) {
            renderImageAndSegment();
            resizeLog();
        }
    });
});

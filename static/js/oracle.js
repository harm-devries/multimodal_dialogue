$(document).ready(function() {
    namespace = $('#namespace').data().name;
    var socket = io.connect('https://' + document.domain + ':' + location.port + namespace, {rememberTransport: false});
    // var QueryString = function () {
    //       // This function is anonymous, is executed immediately and 
    //       // the return value is assigned to QueryString!
    //       var query_string = {};
    //       var query = window.location.search.substring(1);
    //       var vars = query.split("&");
    //       for (var i=0;i<vars.length;i++) {
    //         var pair = vars[i].split("=");
    //             // If first entry with this name
    //         if (typeof query_string[pair[0]] === "undefined") {
    //           query_string[pair[0]] = decodeURIComponent(pair[1]);
    //             // If second entry with this name
    //         } else if (typeof query_string[pair[0]] === "string") {
    //           var arr = [ query_string[pair[0]],decodeURIComponent(pair[1]) ];
    //           query_string[pair[0]] = arr;
    //             // If third or later entry with this name
    //         } else {
    //           query_string[pair[0]].push(decodeURIComponent(pair[1]));
    //         }
    //       } 
    //       return query_string;
    // }();
    // socket.emit('update session', {assignmentId: QueryString.assignmentId,
    //                                hitId: QueryString.hitId,
    //                                workerId: QueryString.workerId});
    
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
    vex.defaultOptions.className = 'vex-theme-default';


    // socket.on('disconnect', function() {
    //     $('#question').hide();
    //     $('#answer').hide();
    //     $('#waiting').hide();
    //     $('#info_text').text('Sorry! The server unexpectedly closed the connection. ');
    //     $('#info_text').show();
    // });
    socket.on('timeout', function() {
        setTimeout(function(){
            window.location.reload(false);
        }, 1000);
    });
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

    socket.on('answerer', function(msg) {
        setTimeout(function(){
            $('#info_text').html('<span class="loader"><span class="loader-inner"></span></span> We have found a partner!');
        }, 700);

        setTimeout(function(){
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
            $('#report').fadeIn(fadeS);
        }, 1400);
    })
    socket.on('new question', function(msg) {
        addQuestion(msg);
        show_answer_form();
    });
    socket.on('start guessing', function(msg) {
        wait_for_guess();
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
        if (msg.qualified) {
            if (msg.finished) {
                $('#newgame_text').html('<p>Congratulations, you have successfully completed this HIT! Please submit your HIT below, and start a new one to continue your streak!</p>');
                $('#qualified').show();
                $('#newgame').hide();
            } else {
                $('#newgame_text').html('<p>Congratulations, you have to finish ' + (10 - msg.stats.success) + ' more games to complete this HIT. </p>');
            }
        } else {
            if (msg.finished) {
                $('#newgame_text').html('<p>Congratulations, you are now qualified to play Guesswhat?! Please submit your HIT below. After that, search for the GuessWhat?! HIT with [QUALIFIED ONLY] and keep playing the game!</p>');
                $('#qualified').show();
                $('#newgame').hide();
            } else {
                $('#newgame_text').html('<p>Congratulations, you have to finish ' + (10 - msg.stats.success) + ' more games to complete this HIT. </p>');
            }
        }
        $('#newgame_text').show();
        $('#intro').show();
        $('#prevbtn').hide();
        set_score(msg.stats.success, msg.stats.failure, msg.stats.oracle_disconnect + msg.stats.oracle_timeout);
    });

    socket.on('wrong annotation', function(msg) {
        deletegame();
        clearInterval(timer_id);
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
        renderSegment(object.segment, scale, segment_ctx, correct_obj);

        $('#info_text').html(text); 
        $('#info_text').fadeIn(fadeS);
        if (msg.qualified) {
            if (msg.blocked) {
                $('#newgame_text').html('<p>You have made too many mistakes to successfully complete this HIT. Please return this HIT and start a new one!</p>');
                $('#newgame').hide();
            } else {
                $('#newgame_text').html('<p>You have to finish ' + (10 - msg.stats.success) + ' more games to complete this HIT. </p>');
            }
        } else {
            if (msg.blocked) {
                $('#newgame_text').html('<p>You have made too many mistakes or disconnected too many times to successfully complete this HIT. Contact Harm de Vries at guesswhat.mturk@gmail.com for more information about your account (include your worker id). </p>');
                $('#newgame').hide();
            } else {
                $('#newgame_text').html('<p>You have to finish ' + (10 - msg.stats.success) + ' more games to complete this HIT. </p>');
            }
        }
        $('#newgame_text').show();
        $('#intro').show();
        $('#prevbtn').hide();
        set_score(msg.stats.success, msg.stats.failure, msg.stats.oracle_disconnect + msg.stats.oracle_timeout);
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
            // socket.emit('timeout');
            clearInterval(timer_id);
            // setTimeout(function(){
            //     window.location.reload(false);
            // }, 3000);
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
        $('#group').fadeOut(fadeS);
        $('#intro').fadeOut(fadeS);
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
        $('#left').switchClass("col-sm-9", "col-sm-5", 0, "easeInOutQuad");
        $('#right').switchClass("col-sm-3", "col-sm-7", 0, "easeInOutQuad");

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

    function modifyAnswer(r, cur_ans) {
        $('#a'+r).text('');
        if (cur_ans == 'Yes') {
            var yes = $(colorizeAnswer(cur_ans)).css('margin-left', '10px');
        } else {
            var yes = $('<a href="#" class="btn btn-success">Yes</a>').on('click', function(){updateAnswer(r, cur_ans, 'Yes')});
        }
        $('#a'+r).append(yes);
        if (cur_ans == 'No') {
            var no = $(colorizeAnswer(cur_ans)).css('margin-left', '10px');
        } else {
            var no = $('<a href="#" style="margin-left: 10px" class="btn btn-danger">No</a>').on('click', function(){updateAnswer(r, cur_ans, 'No')});
        }
        $('#a'+r).append(no);
        if (cur_ans == 'N\/A') {
            var na = $(colorizeAnswer(cur_ans)).css('margin-left', '10px');
        } else {
            var na = $('<a href="#" style="margin-left: 10px" class="btn btn-info">Not applicable</a>').on('click', function(){updateAnswer(r, cur_ans, 'Not applicable')});
        }
        $('#a'+r).append(na);
    }

    function colorizeAnswer(msg, line_through) {
        if (msg == 'Yes') {
            if (!line_through) {
                msg = '<span style="color: #61b832">Yes</span>';
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
        socket.emit('update answer', {round: r, old_msg: old_msg, new_msg: new_msg})
    }

    function addAnswer(msg){
        col_msg = colorizeAnswer(msg);
        if (round % 2 == 0) {
            var cur_round = round;
            var ans = $('<div id="a' + cur_round + '" class="well well-sm" style="font-weight: 500">' + col_msg +'</div>')
            var link = $('<span style="float: right"><i class="fa fa-undo"></i> <a href="#">Undo</a></span>').click(function(){modifyAnswer(cur_round, msg)}).appendTo(ans);
            $('#q'+round).after(ans);
        } else {
            var cur_round = round;
            var ans = $('<div id="a' + cur_round + '" class="well well-sm" style="font-weight: 500; background-color: #fff;">' + col_msg +'</div>')
            var link = $('<span style="float: right"><i class="fa fa-undo"></i> <a href="#">Undo</a></span>').click(function(){modifyAnswer(cur_round, msg)}).appendTo(ans);
            $('#q'+round).after(ans);
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
          message: 'This will end the game.',             // adds the content message
          placeholder: 'Please specify a reason',      // text displayed in Prompt input field

          // calls a callback function, with simple Alert message
          // if the user adds data in the input field, "value" contains that text, if Cancel, value is false,
          // if OK with no data added in input field, value is an object with empty "vex" property
          callback: function(value) {
            if(value !== false && value != '') {
                deletegame(); 
                noPartner(); 
                socket.emit('report questioner', value);
            }
          }
        });
    });
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
        if (img != undefined) {
            scale = get_scale($('#image').width(), img.width, $('.center-container').height() - 15, img.height);
            var new_width = parseInt(img.width*scale);
            var new_height = parseInt(img.height*scale);
            set_canvas_size(img_canvas, new_width, new_height);
            renderImage(img_canvas, img_ctx, img.src, new_width, new_height);
            set_canvas_size(segment_canvas, new_width, new_height);
            if (show_obj) {
                renderSegment(object.segment, scale, segment_ctx, correct_obj);
            }
        }
    }

    $(window).resize(function() {
        if (img != undefined) {
            renderImageAndSegment();
            resizeLog();
        }
    });
});

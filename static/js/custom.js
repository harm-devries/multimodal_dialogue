$(document).ready(function(){
    namespace = '/game';
    var socket = io.connect('http://' + document.domain + ':' + location.port + namespace);
    var image_src; //image url
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
    var question_time = 60;
    var guess_time = 30;


    socket.on('disconnect', function() {
        $('#question').hide();
        $('#answer').hide();
        $('#waiting').hide();
        $('#info_text').text('Sorry! The server unexpectedly closed the connection. ');
        $('#info_text').show();
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

    socket.on('questioner', function(msg) {
        setTimeout(function(){
            $('#info_text').html('<span class="loader"><span class="loader-inner"></span></span> We have found a partner! You are the <b style="font-weight: 700">questioner</b>.');
        }, 1000);
        
        setTimeout(function(){
            $('#title').fadeOut(fadeS);
            $('#intro').fadeOut(fadeS);
            $('#info_text').hide();
            $('#waiting_text').text('Waiting for an answer..');
            $('#waiting').hide();
            image_src = msg.img;
            $('#image').show();
            renderImage();
            show_question_form();
            $('#score').fadeIn(fadeS);
        }, 2000);
        
    })
    socket.on('answerer', function(msg) {
        setTimeout(function(){
            $('#info_text').html('<span class="loader"><span class="loader-inner"></span></span> We have found a partner! You are the <b style="font-weight: 700">oracle</b>.');
        }, 1000);

        setTimeout(function(){
            $('#title').fadeOut(fadeS);
            $('#intro').fadeOut(fadeS);
            $('#info_text').hide();
            image_src = msg.img;
            object = msg.object;
            correct_obj = true;
            $('#image').show();
            renderImage();
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
    socket.on('new answer', function(msg) {
        addAnswer(msg);
        show_question_form();
    });
    socket.on('all annotations', function(msg) {
        if (msg.partner) {
            wait_for_guess();
        } else {
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
        }
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
        if (msg.partner) {
            text = '<i class="fa fa-check-circle fa-2x"></i> <h3 style="margin-left: 10px; display: inline">Correct!</h3>';
        } else {
            text = '<i class="fa fa-check-circle fa-2x"></i> <h3 style="margin-left: 10px; display: inline">Correct!</h3>';
        }
        $('#intro').html('In the winning mood? Play a new game by clicking on the button below.');
        $('#intro').fadeIn(fadeS); 
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
        if (msg.partner) {
            correct_obj = false;
            text = '<i class="fa fa-times-circle fa-2x"></i> <h3 style="margin-left: 10px; display:inline">Incorrect!</h3> <span style="float: right; line-height: 35px;">Your partner guessed:</span>';
        } else {
            text = '<i class="fa fa-times-circle fa-2x"></i> <h3 style="margin-left: 10px; display:inline">Incorrect!</h3> <span style="float: right; line-height: 35px;">The correct object was:</span>';
            correct_obj = true;
        }

        // set object
        object = msg.object;
        set_object();
        renderSegment(object.segment, scale, segment_ctx);

        $('#info_text').html(text); 
        $('#info_text').fadeIn(fadeS);
        $('#intro').text('Do you want revenge? Play a new game by clicking on the button below.');
        $('#intro').fadeIn(fadeS);
        $('#p_newgame').show();
    });

    function wait_for_question() {
        $('#answer').hide();
        $('#waiting').show();
        time = question_time;
        clearInterval(timer_id);
        set_time('#w_time');
        timer_id = setInterval(set_time.bind(null, '#w_time'), 1000);
    }

    function wait_for_answer() {
        $('#question').hide();
        $('#waiting').show();
        $('#newquestion').val('');
        time = answer_time;
        clearInterval(timer_id);
        set_time('#w_time');
        timer_id = setInterval(set_time.bind(null, '#w_time'), 1000);
    }

    function wait_for_guess() {
        $('#waiting_text').text('Your partner started guessing..');
        $('#waiting').show();
        time = guess_time;
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
                window.location = '/game';
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
        // $('#left').switchClass("col-sm-9", "col-sm-5", 0, "easeInOutQuad");
        // $('#right').switchClass("col-sm-3", "col-sm-7", 0, "easeInOutQuad");

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

    function renderImage() {
        var im = new Image();
        var max_width = $('#image').width();
        var max_height = $('.center-container').height() - 15;

        im.onload = function() {
            var width_scale = max_width/im.width;
            var height_scale = max_height/im.height;
            scale = Math.min(width_scale, height_scale);
            var new_height = parseInt(im.height*scale);
            var new_width = parseInt(im.width*scale);
            img_canvas.width = new_width;
            img_canvas.height = new_height;
            segment_canvas.width = new_width;
            segment_canvas.height = new_height;
            roundedImage(img_ctx, 0, 0, new_width, new_height, 5); //Rounded corners
            img_ctx.clip();
            img_ctx.drawImage(im, 0, 0, new_width, new_height); //Draw image
            if (objs != null) {
                renderSegments(objs, scale, segment_ctx);
            }
            if (object != null && show_obj) {
                renderSegment(object.segment, scale, segment_ctx);
            }
        }
        im.src = image_src;
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
        noPartner();
        socket.emit('next');
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
    $("#guessinput").keyup(function(event){
        if(event.keyCode == 13){
            $("a#guessbtn").click();
        }
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

    function getMousePosition(e){
        var canvasOffset = $("canvas#segment").offset();
        mouseX = parseInt(e.clientX - canvasOffset.left);
        mouseY = parseInt(e.clientY - canvasOffset.top);
        return [mouseX, mouseY]
    }

    function getObjectFromClick(mouseX, mouseY, objs, scale) {
        for (var i = 0; i< objs.length; i++) {
            obj = objs[i];
            for(j=0; j<obj.segment.length; j++){
                coords_x = obj.segment[j].x;
                coords_y = obj.segment[j].y;
                if (inside(mouseX, mouseY, coords_x, coords_y, scale)) {
                    return obj.object_id;
                }
            }
        }
        return undefined;
    }

    /* Render single segmentation for oracle */
    function renderSegment(segment, scale, ctx){
        // set color for each object
        var r, g, b;
        if (correct_obj) {
            r = 0;
            g = 255;
        } else {
            r = 255;
            g = 0;
        }
        b = 0;
        ctx.fillStyle = 'rgba('+r+','+g+','+b+',0.4)';

        for (j=0; j<segment.length; j++){
            coords_x = segment[j].x;
            coords_y = segment[j].y;
            // let's draw!!!!
            ctx.beginPath();
            ctx.moveTo(parseFloat(coords_x[0]*scale), parseFloat(coords_y[0]*scale));
            for (k=1; k < coords_x.length; k+=1) { 
                ctx.lineTo(parseFloat(coords_x[k]*scale), parseFloat(coords_y[k]*scale));
            }

            ctx.lineWidth = 2;
            ctx.closePath();
            ctx.fill();
            ctx.strokeStyle = 'black';
            ctx.stroke();
        }
    }

    function getHighlightedObjIndex(objs, scale, mouseX, mouseY) {
        for (var i = 0; i< objs.length; i++) {
            obj = objs[i];
            for(j=0; j<obj.segment.length; j++){
                coords_x = obj.segment[j].x;
                coords_y = obj.segment[j].y;
                if (inside(mouseX, mouseY, coords_x, coords_y, scale)) {
                    return i;
                }
            }
        }
        return undefined;
    }

    /* Render all segments for questioner */
    function renderSegments(objs, scale, ctx, mouseX, mouseY) {
        // set color for each object
        var ind;
        if(mouseX != undefined && mouseY != undefined) {
            ind = getHighlightedObjIndex(objs, scale, mouseX, mouseY);
        }
        for(var i = 0; i< objs.length; i++) {
            var r = colors[i][0];
            var g = colors[i][1];
            var b = colors[i][2];
            obj = objs[i];

            if (i == ind) {
                ctx.fillStyle = 'rgba('+r+','+g+','+b+',0.9)';
            } else {
                ctx.fillStyle = 'rgba('+r+','+g+','+b+',0.3)';
            }

            for (var j=0; j<obj.segment.length; j++){
                coords_x = obj.segment[j].x;
                coords_y = obj.segment[j].y;

                ctx.beginPath();
                ctx.moveTo(parseFloat(coords_x[0]*scale), parseFloat(coords_y[0]*scale));
                for (var k=1; k< coords_x.length; k+=1) { 
                    ctx.lineTo(parseFloat(coords_x[k]*scale), parseFloat(coords_y[k]*scale));
                }
                ctx.lineWidth = 2;
                ctx.closePath();
                ctx.fill();
                ctx.strokeStyle = 'black';
                ctx.stroke();
            }
        }
        if (ind != undefined) {
            $('canvas#segment').css('cursor', 'pointer');
        } else {
            $('canvas#segment').css('cursor', 'default');
        }
    }

    function clearCanvas(ctx, canvas) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
    }

    function inside(x, y, poly_x, poly_y, scale) {
        // ray-casting algorithm based on
        // http://www.ecse.rpi.edu/Homepages/wrf/Research/Short_Notes/pnpoly.html
        var inside = false;
        for (var i = 0, j = poly_x.length - 1; i < poly_x.length; j = i++) {
            var xi = poly_x[i]*scale, yi = poly_y[i]*scale;
            var xj = poly_x[j]*scale, yj =poly_y[j]*scale;

            var intersect = ((yi > y) != (yj > y))
                && (x < (xj - xi) * (y - yi) / (yj - yi) + xi);
            if (intersect) inside = !inside;
        }
        return inside;
    }

    function roundedImage(ctx, x, y, width, height, radius) {
        ctx.beginPath();
        ctx.moveTo(x + radius, y);
        ctx.lineTo(x + width - radius, y);
        ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
        ctx.lineTo(x + width, y + height - radius);
        ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
        ctx.lineTo(x + radius, y + height);
        ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
        ctx.lineTo(x, y + radius);
        ctx.quadraticCurveTo(x, y, x + radius, y);
        ctx.closePath();
    }

    function scrollBottom() {
        $('#log').scrollTop(0);
    }

    function resizeLog() {
        $('#log').height($('.center-container').height() - 15);
        scrollBottom();
    }

    $(window).resize(function() {
        renderImage();
        resizeLog();
    });
});

$(document).ready(function(){
    namespace = '/game';
    var socket = io.connect('http://' + document.domain + ':' + location.port + namespace);
    var image_src; //image url
    var object; // selected object for oracle
    var scale; // scale of image compared to original size
    var img_canvas = $('canvas#img')[0];
    var img_ctx = img_canvas.getContext("2d");
    var segment_canvas = $('canvas#segment')[0];
    var segment_ctx = segment_canvas.getContext("2d");
    var objs; // All annotations. Only defined after questioner pressed guess button
    var no_partner = false;
    var partner_disconnect = false;
    var colors = [[255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 0], [255, 0, 255], 
                  [255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 0], [255, 0, 255], 
                  [255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 0], [255, 0, 255],
                  [255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 0], [255, 0, 255],
                  [255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 0], [255, 0, 255],
                  [255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 0], [255, 0, 255]];
    var fadeS = 600;

    socket.on('disconnect', function() {
        hideAll();
        $('#waiting_text').text('Sorry! The server unexpectedly closed the connection. ');
        $('#waiting').show();
    });
    socket.on('partner_disconnect', function() {
        hideAll();
        partner_disconnect = true;
        deletegame();
    });
    socket.on('no partner', function(msg) {
        no_partner = true;
        noPartner();
    })
    socket.on('questioner', function(msg) {
        if (!no_partner) {
            noPartner();
            no_partner = false;
        }

        setTimeout(function(){
            $('#waiting_text').html('We have found a partner! You are the <b>questioner</b>.');
        }, 2000);
        
        setTimeout(function(){
            $('#waiting_text').text('Waiting for an answer..');
            $('#waiting').hide();
            image_src = msg.img;
            $('#image').show();
            renderImage();
            $('#newquestion').focus();
            $('#question').fadeIn(fadeS);
            $('#newquestion').focus();
            $('#guess').fadeIn(fadeS);

        }, 4000);
        
    })
    socket.on('answerer', function(msg) {
        if (!no_partner) {
            noPartner();
            no_partner = false;
        }

        setTimeout(function(){
            $('#waiting_text').html('We have found a partner! You are the <b>oracle</b>.');
        }, 2000);

        setTimeout(function(){
            $('#title').fadeOut(fadeS);
            $('#intro').fadeOut(fadeS);
            image_src = msg.img;
            object = msg.object;
            console.log(object);
            console.log(msg);
            $('#image').show();
            renderImage();
            $('#waiting_text').text('Waiting for a new question');
            $('#waiting').fadeIn(fadeS);
            $('#object').html('<img width="35px" height="35px" src="http://mscoco.org/static/icons/' + object.category_id + '.jpg" /> ' + object.name);
            $('#object').fadeIn(fadeS);
            $('#object').hover(function(){
                clearCanvas(segment_ctx, segment_canvas);
            },
            function(){
                renderSegment(object.segment, scale, segment_ctx);
            });
        }, 3500);

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
        $('#newquestion').focus();
    });
    socket.on('all annotations', function(msg) {
        if (msg.partner) {
            $('#waiting_text').text('Your partner started guessing the object!');
            $('#waiting').show();
        } else {
            objs = msg.objs;
            renderSegments(objs, scale, segment_ctx);
            $('#question').hide();
            $('#guess').hide();
            $('#object').html('<h3>Please click on one of the objects in the image below.</h3>');
            $('#object').show();
        }
    });
    socket.on('correct annotation', function(msg) {
        hideAll();
        infoBarUp();
        $('#guessinput').val(''); 
        if (msg.partner) {
            text = 'Your partner has guessed the correct object. ';
        } else {
            text = 'You have guessed the correct object.';
        }
        $('#title').html('<h2>Congratulations!</h2>');
        $('#title').fadeIn(fadeS);
        $('#intro').html(text);
        $('#intro').fadeIn(fadeS); 
        $('#p_newgame').show();
        deletegame();
    });
    socket.on('wrong annotation', function(msg) {
        hideAll();
        infoBarUp();
        $('#guessinput').val(''); 
        if (msg.partner) {
            text = 'Your partner has guessed the wrong object.';
        } else {
            text = 'You have guessed the wrong object. ';
        }
        $('#title').html('<h2>Game over!</h2>');
        $('#title').fadeIn(fadeS);
        $('#intro').html(text);
        $('#intro').fadeIn(fadeS); 
        $('#p_newgame').show();
        deletegame();
    });

    function deletegame() {
        poly_x = null;
        poly_y = null;
        objs = null;
        $('#log').html('');
        $('#log').show();
    }

    function hideAll() {
        $('#log').hide();
        $('#intro').hide();
        $('#answer').hide();
        $('#question').hide();
        $('#waiting').hide();
        $('#guess').hide();
        $('#image').hide();
        $('#object').hide();
    }

    function noPartner() {
        $('#title').fadeOut(fadeS);
        $('#intro').fadeOut(fadeS);
        if(partner_disconnect) {
            $('#waiting_text').text('Your partner disconnected. Waiting for a new partner..');
            partner_disconnect = false;
        } else {
            $('#waiting_text').text('Searching for a partner..');
        }
        
        $('#waiting').show();
        infoBarDown();
    }

    function infoBarDown() {
        $('body').animate({
            paddingTop: "120px"
        }, 1000);
        $('#info').animate({
            height: "60px",
            paddingTop: "10px",
            paddingBottom: "10px" 
        }, 1000);
        // $('#left').switchClass("col-sm-9", "col-sm-5", 0, "easeInOutQuad");
        // $('#right').switchClass("col-sm-3", "col-sm-7", 0, "easeInOutQuad");

    }
    function infoBarUp() {
        $('body').animate({
            paddingTop: "50px"
        }, 1000);
        $('#info').animate({
            height: "0px",
            paddingTop: "0px",
            paddingBottom: "0px" 
        }, 1000);
        // $('#left').switchClass("col-sm-5", "col-sm-9", 0, "easeInOutQuad");
        // $('#right').switchClass("col-sm-7", "col-sm-3", 0, "easeInOutQuad");

    }

    function addAnswer(msg){
        $('#log').prepend('<div class="well well-sm">' + msg + '</div>');
        scrollBottom();
    }
    function addQuestion(msg){
        $('#log').prepend('<div class="well well-sm">' + msg + '</div>');
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
            if (object != null) {
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
        msg = 'Yes'
        addAnswer(msg);
        $('#answer').hide();
        $('#waiting').fadeIn(1000);
        socket.emit('new answer', msg);
        return false;
    });
    $('a#no').click(function(event) {
        msg = 'No'
        addAnswer(msg);
        $('#answer').hide();
        $('#waiting').fadeIn(1000);
        socket.emit('new answer', msg);
        return false;
    });
    $('a#na').click(function(event) {
        msg = 'Not applicable'
        addAnswer(msg);
        $('#answer').hide();
        $('#waiting').fadeIn(1000);
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
            if (id != null) {
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
        return null;
    }

    /* Render single segmentation for oracle */
    function renderSegment(segment, scale, ctx){
        // set color for each object
        var r = 255;
        var g = 0;
        var b = 0;
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
        return null;
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
        if (k!= undefined) {
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
        log.scrollTop = $('#log').offset().top;
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
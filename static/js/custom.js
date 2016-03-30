$(document).ready(function(){
    namespace = '/game';
    var socket = io.connect('http://' + document.domain + ':' + location.port + namespace);
    var image_src;
    var poly_x;
    var poly_y;
    var scale;
    var img_canvas = $('canvas#img')[0];
    var img_ctx = img_canvas.getContext("2d");
    var segment_canvas = $('canvas#segment')[0];
    var segment_ctx = segment_canvas.getContext("2d");
    var objs;
    var colors = [[255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 0], [255, 0, 255], 
                  [0, 255, 255], [0, 255, 255], [0, 255, 255], [0, 255, 255], [0, 255, 255], 
                  [0, 255, 255], [0, 255, 255], [0, 255, 255], [0, 255, 255]];

    socket.on('disconnect', function() {
        hideAll();
        $('#intro').html('<div class="well">The server unexpectedly closed the connection</div>');
        $('#intro').show();
    });
    socket.on('partner_disconnect', function() {
        hideAll();
        poly_x = null;
        poly_y = null;
        objs = null;
        $('#log').html('');
        $('#log').show();
        $('#intro').html('<div class="well">Sorry! Your partner unexpectedly closed the game.</div>');
        $('#intro').show();
    });
    socket.on('no partner', function(msg) {
        $('#title').hide();
        $('#intro').html('<div class="well"><span class="loader"><span class="loader-inner"></span></span> Waiting for a new partner...</div>');
    })
    socket.on('questioner', function(msg) {
        $('#title').hide();
        $('#intro').hide();
        $('#waiting_text').text('Waiting for an answer');
        image_src = msg.img;
        renderImage();
        $('#question').show()
        $('#guess').show();
    })
    socket.on('answerer', function(msg) {
        $('#title').hide();
        $('#intro').hide();
        image_src = msg.img;
        poly_x = msg.poly_x;
        poly_y = msg.poly_y;
        renderImage();
        $('#waiting_text').text('Waiting for a new question');
        $('#waiting').show();
        $('#object').html('<img width="40px" height="40px" src="http://mscoco.org/static/icons/' + msg.catid + '.jpg" /> Your object is ' + msg.name);
        $('#object').show();
        $('#object').hover(function(){
            renderSegment(poly_x, poly_y, scale, segment_ctx);
        },
        function(){
            clearCanvas(segment_ctx, segment_canvas);
        });

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
    socket.on('correct answer', function(msg) {
        if (msg.partner) {
            $('#waiting_text').text('Congratulations. Your partner has guessed the correct object! ');
            $('#waiting').show();
        } else {
            objs = msg.objs;
            renderSegments(objs, scale, segment_ctx);
            $('#question').hide();
            $('#guess').hide();
            $('#object').text('Correct! Please click on the correct annotation in the image above.');
            $('#object').show();
        }
    });
    socket.on('incorrect answer', function(msg) {
        hideAll();
        $('#guessinput').val(''); 
        if (msg.partner) {
            text = 'Game over! Your partner incorrectly guessed <strong>' + msg.obj + '</strong>';
        } else {
            text = 'Game over! You incorrectly guessed <strong>' + msg.obj + '</strong>';
        }
        $('#intro').html('<div class="well">'+text+'</div>');
        $('#intro').show(); 
    });
    socket.on('correct annotation', function(msg) {
        hideAll();
        $('#guessinput').val(''); 
        if (msg.partner) {
            text = 'Congratulations! Your partner has guessed the correct object. ';
        } else {
            text = 'Congratulations! You have guessed the correct object.';
        }
        $('#intro').html('<div class="well">'+text+'</div>');
        $('#intro').show(); 
    });
    socket.on('wrong annotation', function(msg) {
        hideAll();
        $('#guessinput').val(''); 
        if (msg.partner) {
            text = 'Game over! Your partner has guessed the wrong object.';
        } else {
            text = 'Game over! You have guessed the wrong object. ';
        }
        $('#intro').html('<div class="well">'+text+'</div>');
        $('#intro').show(); 
    });

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

    function addAnswer(msg){
        $('#log').append('<div class="well well-sm">' + msg + '</div>');
        scrollBottom();
    }
    function addQuestion(msg){
        $('#log').append('<div class="well well-sm">' + msg + '</div>');
        scrollBottom();
    }

    function renderImage() {
        $('#image').show();
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
        }
        im.src = image_src;
    }

    // event handler for server sent data
    // the data is displayed in the "Received" section of the page
    // handlers for the different forms in the page
    // these send data to the server in a variety of ways
    
    $('a#guessbtn').click(function(event) {
        $('#guessbtn').attr('disabled', false); 
        var obj = $('#guessinput').val();
        socket.emit('guess', obj);
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
        msg = '<span class="text-success">Yes</span>'
        addAnswer(msg);
        $('#answer').hide();
        $('#waiting').fadeIn(1000);
        socket.emit('new answer', msg);
        return false;
    });
    $('a#no').click(function(event) {
        msg = '<span class="text-warning">No</span>'
        addAnswer(msg);
        $('#answer').hide();
        $('#waiting').fadeIn(1000);
        socket.emit('new answer', msg);
        return false;
    });
    $('a#na').click(function(event) {
        msg = '<span class="text-info">Not applicable</span>'
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
        for(i = 0; i < objs.length; i++) {
            poly_x = objs[i].poly_x;
            poly_y = objs[i].poly_y;
            for(j=0; j<poly_x.length; j++) {
                px = poly_x[j];
                py = poly_y[j];

                if (inside(mouseX, mouseY, px, py, scale)) {
                    return objs[i].id;
                }
            }
        }
        return null;
    }

    /* Render single segmentation for oracle */
    function renderSegment(poly_x, poly_y, scale, ctx){
        // set color for each object
        var r = 255;
        var g = 0;
        var b = 0;
        ctx.fillStyle = 'rgba('+r+','+g+','+b+',0.4)';

        for (j=0; j<poly_x.length; j++){
            px = poly_x[j];
            py = poly_y[j];
            // let's draw!!!!
            ctx.beginPath();
            ctx.moveTo(parseFloat(px[0]*scale), parseFloat(py[0]*scale));
            for (k=1; k< px.length; k+=1) { 
                ctx.lineTo(parseFloat(px[k]*scale), parseFloat(py[k]*scale));
            }

            ctx.lineWidth = 2;
            ctx.closePath();
            ctx.fill();
            ctx.strokeStyle = 'black';
            ctx.stroke();
        }
    }

    /* Render all segments for questioner */
    function renderSegments(objs, scale, ctx, mouseX, mouseY){
        // set color for each object
        highlight = false;
        for(i = 0; i< objs.length; i++) {
            var r = colors[i][0];
            var g = colors[i][1];
            var b = colors[i][2];
            poly_x = objs[i].poly_x;
            poly_y = objs[i].poly_y;

            var highlight_obj = false;
            if (mouseX != undefined && mouseY != undefined && !highlight) {
                for(j=0; j<poly_x.length; j++){
                    px = poly_x[j];
                    py = poly_y[j];

                    if (inside(mouseX, mouseY, px, py, scale)) {
                        highlight_obj = true;
                        highlight = true;
                    }
                }
            }

            if (highlight_obj) {
                ctx.fillStyle = 'rgba('+r+','+g+','+b+',0.9)';
            } else {
                ctx.fillStyle = 'rgba('+r+','+g+','+b+',0.3)';
            }

            for (j=0; j<poly_x.length; j++){
                px = poly_x[j];
                py = poly_y[j];

                // let's draw!!!!
                ctx.beginPath();
                ctx.moveTo(parseFloat(px[0]*scale), parseFloat(py[0]*scale));
                for (k=1; k< px.length; k+=1) { 
                    ctx.lineTo(parseFloat(px[k]*scale), parseFloat(py[k]*scale));
                }
                ctx.lineWidth = 2;
                ctx.closePath();
                ctx.fill();
                ctx.strokeStyle = 'black';
                ctx.stroke();
            }
        }
        if (highlight) {
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
        log = document.getElementById('log');
        log.scrollTop = log.scrollHeight - log.clientHeight;
    }

    function resizeLog() {
        $('#log').height($('.center-container').height() - 15);
        scrollBottom();
    }

    $(window).resize(function() {
        renderImage();
        resizeLog();
    });

    // var substringMatcher = function(strs) {
    //   return function findMatches(q, cb) {
    //     var matches, substringRegex;

    //     // an array that will be populated with substring matches
    //     matches = [];

    //     // regex used to determine if a string contains the substring `q`
    //     substrRegex = new RegExp(q, 'i');

    //     // iterate through the pool of strings and for any string that
    //     // contains the substring `q`, add it to the `matches` array
    //     $.each(strs, function(i, str) {
    //       if (substrRegex.test(str)) {
    //         matches.push(str);
    //       }
    //     });

    //     cb(matches);
    //   };
    // };

    // var states = ['Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California',
    //   'Colorado', 'Connecticut', 'Delaware', 'Florida', 'Georgia', 'Hawaii',
    //   'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana',
    //   'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota',
    //   'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada', 'New Hampshire',
    //   'New Jersey', 'New Mexico', 'New York', 'North Carolina', 'North Dakota',
    //   'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island',
    //   'South Carolina', 'South Dakota', 'Tennessee', 'Texas', 'Utah', 'Vermont',
    //   'Virginia', 'Washington', 'West Virginia', 'Wisconsin', 'Wyoming'
    // ];
    // var states = new Bloodhound({
    //   datumTokenizer: Bloodhound.tokenizers.whitespace,
    //   queryTokenizer: Bloodhound.tokenizers.whitespace,
    //   // `states` is an array of state names defined in "The Basics"
    //   local: states
    // });

    // $('#guessinput').typeahead({
    //   hint: true,
    //   highlight: true,
    //   minLength: 1
    // },
    // {
    //   name: 'states',
    //   source: states
    // });
});
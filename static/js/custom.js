$(document).ready(function(){
    namespace = '/game';
    var socket = io.connect('https://' + document.domain + ':' + location.port + namespace);
    var image_src;
    var poly_x;
    var poly_y;

    socket.on('disconnect', function() {
        hideAll();
        $('#intro').html('<div class="well">The server unexpectedly closed the connection</div>');
    });
    socket.on('partner_disconnect', function() {
        hideAll();
        poly_x = null;
        poly_y = null;
        $('.log').html('');
        $('#intro').html('<div class="well">Sorry! Your partner unexpectedly closed the game.</div>');
        $('#intro').show();
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
        image_src = msg.img;
        renderImage();
        $('#question').show()
        $('#guess').show();
    })
    socket.on('answerer', function(msg) {
        $('#intro').hide();
        image_src = msg.img;
        poly_x = msg.poly_x;
        poly_y = msg.poly_y;
        renderImage();
        $('#waiting_text').text('Waiting for a new question');
        $('#waiting').show();
        $('#object').html('<div class="well">Your object is ' + msg.name);
        $('#object').show();

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
    socket.on('correct_answer', function(msg) {
        hideAll();
        if (msg.partner) {
            $('#intro').html('<div class="well">Congratulations! Your partner have guessed the correct object!</div>');
        } else {
            $('#intro').html('<div class="well">Congratulations! You have guessed the correct object!</div>');
        }
        $('#intro').show();
    });
    socket.on('incorrect_answer', function(msg) {
        if (msg.partner) {
            text = 'Your partner incorrectly guessed <strong>' + msg.obj + '</strong>';
        } else {
            text = 'You incorrectly guessed <strong>' + msg.obj + '</strong>';
        }
        $('.log').prepend('<hr style="margin-top: 0;"><div class="row"><div class="col-sm-1"><h3>G:</h3></div><div class="well well-sm col-sm-11">' + text + '</div></div>');
        $('#guessinput').val(''); 
        $('#guessbtn').attr('disabled', false); 
    });

    function hideAll() {
        $('.log').hide();
        $('#intro').hide();
        $('#answer').hide();
        $('#question').hide();
        $('#waiting').hide();
        $('#guess').hide();
        $('#image').hide();
        $('#object').hide();
    }

    function addAnswer(msg){
        $('.log').prepend('<hr style="margin-top: 0;"><div class="row"><div class="col-sm-1"><h3>A:</h3></div><div class="well well-sm col-sm-11">' + msg + '</div></div>');
    }
    function addQuestion(msg){
        $('.log').prepend('<div class="row"><div class="col-sm-1"><h3>Q:</h3></div><div class="well well-sm col-sm-11">' + msg + '</div></div>');
    }

    function renderImage() {
        $('#title').hide();
        $('.log').show();

        $('#image').show();
        var canvas = $('canvas#img')[0];
        var ctx = canvas.getContext("2d");
        var im = new Image();
        var new_width = $('#image').width();

        im.onload = function() {
            var scale = new_width/im.width;
            var new_height = parseInt(im.height*scale);
            canvas.width = new_width;
            canvas.height = new_height;
            roundedImage(ctx, 0, 0, new_width, new_height, 5); //Rounded corners
            ctx.clip();
            ctx.drawImage(im, 0, 0, new_width, new_height); //Draw image
            if (poly_x != null) {
                renderSegmentation(poly_x, poly_y, scale, ctx); // Render segmentation
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

    function renderSegmentation(poly_x, poly_y, scale, ctx){
        // set color for each object
        var r = 255;
        var g = 0;
        var b = 0;
        ctx.fillStyle = 'rgba('+r+','+g+','+b+',0.7)';

        for (j=0; j<poly_x.length; j++){
            px = poly_x[j];
            py = poly_y[j];
            // let's draw!!!!
            ctx.beginPath();
            ctx.moveTo(parseFloat(px[0]*scale), parseFloat(py[0]*scale));
            for (k=1; k< px.length; k+=1) { 
                ctx.lineTo(parseFloat(px[k]*scale), parseFloat(py[k]*scale));
            }

            ctx.lineWidth = 3;
            ctx.closePath();
            ctx.fill();
            ctx.strokeStyle = 'black';
            ctx.stroke();
        }
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

    $(window).resize(function() {
        renderImage();
    });
});
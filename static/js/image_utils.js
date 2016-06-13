var scale;
var colors = [[0, 255, 0], [255, 0, 0], [0, 0, 255], [255, 255, 0], [255, 0, 255], 
                  [255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 0], [255, 0, 255], 
                  [255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 0], [255, 0, 255],
                  [255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 0], [255, 0, 255],
                  [255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 0], [255, 0, 255],
                  [255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 0], [255, 0, 255]];

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

function get_scale(max_width, im_width, max_height, im_height) {
    var width_scale = max_width/im_width;
    var height_scale = max_height/im_height;
    return Math.min(width_scale, height_scale);
}

function set_canvas_size(img_canvas, new_width, new_height) {
    img_canvas.width = new_width;
    img_canvas.height = new_height;
}

function renderImage(img_canvas, img_ctx, image_src, width, height) {
    var im = new Image();

    im.onload = function() {
        roundedImage(img_ctx, 0, 0, width, height, 5); //Rounded corners
        img_ctx.clip();
        img_ctx.drawImage(im, 0, 0, width, height); //Draw image
    }
    im.src = image_src;
}

/* Render single segmentation for oracle */
function renderSegment(segment, scale, ctx, correct_obj){
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
    for(var i = objs.length-1; i >= 0; i--) {
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
    $('#log').height($('.center-container').height() - 30);
    scrollBottom();
}

// $(window).resize(function() {
//     renderImage();
//     resizeLog();
// });
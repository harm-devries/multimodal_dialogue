/**
 * Created by fstrub on 04/10/16.
 */



$(document).ready(function() {


    //require to load theme
    vex.defaultOptions.className = 'vex-theme-default';

    $('.show_dialogue').click(function (event) {

        var row_id = $(this).attr("value")
        var logs = $("#log_"+row_id)

        vex.dialog.alert({
            message : 'The dialogue that lead to the question.',
            input : '<div id="dialogue_vex"></div>',
            afterOpen: function() {
                $(".vex-content").css("width", "800px")
                logs.clone().show().appendTo($("#dialogue_vex"))
            }
        });
    });
    
    $(".fixed_question" ).focusout(function() {

        var row_line = $(this).attr("name").match(/\d+/);
        var question = $("#span_"+row_line).text();
        var question_fixed = $(this).val()

        if (question === $(this).val())
        {
            $(this).css("color","orange");
        }
        else if (question_fixed.search($(this).attr("pattern")) == 0 )
        {
            $(this).css("color","green");
        }
        else
        {
            $(this).css("color","red");
        }

    });


    //disable copy/past source : http://stackoverflow.com/questions/9958478/how-to-disable-copy-paste-browser

    //disable mouse drag select start
    document.onselectstart = new Function('return false');
    function dMDown(e) { return false; }
    //function dOClick() { return true; }
    //document.onmousedown = dMDown;
    //document.onclick = dOClick;

    $("#document").attr("unselectable", "on");

    //disable mouse drag select end  disable right click - context menu
    document.oncontextmenu = new Function("return false");

    //disable CTRL+A/CTRL+C through key board start
    function disableSelectCopy(e) {
    // current pressed key
        var pressedKey = String.fromCharCode(e.keyCode).toLowerCase();
        if (e.ctrlKey && (pressedKey == "c" || pressedKey == "x" || pressedKey == "v" || pressedKey == "a")) {
            return false;
        }

    }

    document.onkeydown = disableSelectCopy;

});
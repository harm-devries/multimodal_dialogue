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
        var question = $("#original_"+row_line).text();
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


});
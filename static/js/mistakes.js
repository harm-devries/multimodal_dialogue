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
            message : 'The dialogue leading to the question.',
            input : '<div id="dialogue_vex"></div>',
            afterOpen: function() {
                $(".vex-content").css("width", "800px")
                logs.clone().show().appendTo($("#dialogue_vex"))
            }
        });
    });
    
});

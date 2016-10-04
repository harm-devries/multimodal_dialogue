/**
 * Created by fstrub on 04/10/16.
 */



$(document).ready(function() {

    vex.defaultOptions.className = 'vex-theme-default';

    $('.show_dialogue').click(function (event) {


        var row_id = $(this).attr("value")
        var logs = $("#log_"+row_id)

        vex.dialog.alert({
            message : 'The dialogue that lead to the question.',
            input : '<div id="yo"></div>',
            afterOpen: function() {
                $(".vex-content").css("width", "800px")
                logs.clone().show().appendTo($("#yo"))
            }
        });
    });

});
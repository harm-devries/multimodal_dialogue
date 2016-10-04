/**
 * Created by fstrub on 04/10/16.
 */



$(document).ready(function() {

    vex.defaultOptions.className = 'vex-theme-default';
    var socket = io.connect('http://' + document.domain + ':' + location.port, {rememberTransport: false});

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

    $('#submit_button').click(function (event) {

        //TODO check answers

        var all_fix = [];


        $(".row").each(function() {

            var one_fix = new Object();
            one_fix.dialogue_id = $(this).find(".dialogue_id").attr("value")
            one_fix.question_id = $(this).find(".question_id").attr("value")
            one_fix.text = $(this).find(".fixed_question").val()

            all_fix.push(one_fix)

        });

        console.log(all_fix);

        socket.emit('dialogue fix',  all_fix );

        vex.dialog.alert({message : "Thank you for your hit!"});
        
    });

});
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


        // check for missing fix
        one_found = false
        $(".fixed_question").each(function()
        {
            console.log("coucou")

            var msg = $(this).val();
            if (msg == '' || msg.match(/\S+/g).length < 3)
            {
                one_found = true
                $(this).css("border", "1px solid #d66")
            }
            else
            {
                $(this).css("border", "")
            }

        });
        if(one_found)
        {
            $("html, body").animate({ scrollTop: 0 }, "slow");
            vex.dialog.alert({message: 'Please use at least 3 words to fix the question".'});
            return
        }


        //Send data
        var all_fix = [];
        $(".row").each(function() {

            var one_fix = new Object();
            one_fix.dialogue_id = $(this).find(".dialogue_id").attr("value")
            one_fix.question_id = $(this).find(".question_id").attr("value")
            one_fix.text = $(this).find(".fixed_question").val()

            all_fix.push(one_fix)

        });

        socket.emit('dialogue fix',  all_fix );

        // remove the current data from the page
        $(".container").empty()

        vex.dialog.confirm({
            message: 'Thank you for your hit! Do you want to start a new hit?',
            callback: function (value) {
                if (value) {
                    location.reload();  //reload the current page -> not sure whether it really works :)
                }
            }
        });
        
    });

});
$(document).ready(function() {
    var $items = $('#group').children();
    var $current = $items.filter('.current');

    $("#prevbtn").toggle(!$current.is($items.first()));    
    $("#nextbtn").toggle(!$current.is($items.last()));
    $('#newgame').toggle($current.is($items.last()));

    function updateItems(delta)
    {
        var $items = $('#group').children();
        var $current = $items.filter('.current');
        var index = $current.index();
        var newIndex = index+delta;
        // Range check the new index
        newIndex = (newIndex < 0) ? 0 : ((newIndex > $items.length) ? $items.length : newIndex); 
        if (newIndex != index){
            $current.removeClass('current');
            $current = $items.eq(newIndex).addClass('current');
            // Hide/show the next/prev
            $("#prevbtn").toggle(!$current.is($items.first()));    
            $("#nextbtn").toggle(!$current.is($items.last()));
            $('#newgame').toggle($current.is($items.last()));    
        }
    }
    $('#nextbtn').click(function(event) {
        updateItems(1);
    });
    $('#prevbtn').click(function(event) {
        updateItems(-1);
    });
    
});
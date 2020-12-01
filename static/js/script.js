// Copied from materialize
$(document).ready(function () {
$(".button-collapse").sideNav({edge: "right"});
$('.modal').modal();
});

// Function for read time numeric dropdown
$(function(){
    let $select = $(".read_time");
    for (i=1;i<=30;i++){
        $select.append($('<option></option>').val(i).html(i))
    }
});
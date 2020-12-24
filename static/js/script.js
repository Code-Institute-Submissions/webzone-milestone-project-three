// Copied from materialize
$(document).ready(function () {
$(".button-collapse").sideNav({edge: "right"});
$('.modal').modal();
});

// Function to display flash messages
function flashMessages() {
    $(".flash_messages").addClass(".show");
    setTimeout(function() {
        $(".flash_messages").removeClass(".show");
    }, 2000);
}

flashMessages();

// function showFlashMessages() {
//     $(".flash_messages").addClass(".show");
//     setTimeout(function() {
//         $(".flash_messages").removeCremoveClass(".show");
//     }, 2000);
// }

// showFlashMessages();
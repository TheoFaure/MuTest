function call_counter(url) {
    $.ajax({
        type:"GET",
        url:"/framework/compute_answers/",
        success: function(response) {
            var context = JSON.parse(response);
            $('#nb_missing_answers').html(context['nb_missing_answers']);
            $('#acc').html(context['accuracies']);
            $('#error').html("");
        },
        error: function (xhr, ajaxOptions, thrownError) {
            $('#error').html("" + xhr.status + thrownError);
        }
    });
}

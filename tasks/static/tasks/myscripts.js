function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

var csrftoken = getCookie('csrftoken');

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

$.ajaxSetup({
    beforeSend: function (xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

// tasks_body es tbody de la tabla
// esto permite que si se añade un elemento a la tabla dinamicamente
// también se cace el click
$('#tasks_body').on('click', 'input[type="checkbox"]', function () {
    var data = {};
    data.id = $(this).attr('value');
    data.value = $(this).is(':checked') ? 1 : 0;

    console.log(data);

    $.ajax({
        type: "POST",
        url: "/task/mark_as_done/",
        data: data,
        success: function (response) {
            task_row_str = '#task_row_' + data.id;
            $(task_row_str).remove();
            next_task_tr_html = response.next_task_tr;
            if (next_task_tr_html != "") {
                $('#tasks_table tr:last').after(next_task_tr_html);
            }
        }
    }).done(function (data) {
        console.log(data);
    });
});

$('#project_tasks_body').on('click', 'input[type="checkbox"]', function () {
    var data = {};
    data.id = $(this).attr('value');
    data.value = $(this).is(':checked') ? 1 : 0;

    console.log(data);

    $.ajax({
        type: "POST",
        url: "/task/mark_as_done/",
        data: data,
        success: function (response) {
            task_row_str = '#task_row_' + data.id;
            $(task_row_str).remove();
        }
    }).done(function (data) {
        console.log(data);
    });
});

$(document).on('click', 'a.confirm-delete', function (event) {
    event.preventDefault();
    confirm('Are you sure you want to delete this?');

    var data = {};
    href = $(this).attr('href');
    data.id = href.split('/')[2]

    $.ajax({
        type: "POST",
        url: "/task/" + data.id + "/delete/",
        data: data,
        success: function (json) {
            task_row_str = '#task_row_' + data.id;
            $(task_row_str).remove();
        }
    }).done(function (data) {
        console.log(data);
    });
});

$(document).on('click', '#new_task_button', function (event) {
    $('#embeded_task_form_div').toggle('slow');
});
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
    tasks_count = parseInt($('#tasks_count').text());

    console.log(data);

    $.ajax({
        type: "POST",
        url: "/tasks/mark_as_done/",
        data: data,
        success: function (response) {
            task_row_str = '#tasks_row_' + data.id;
            $(task_row_str).remove();
            tasks_count = tasks_count - 1;
            for (next_task_tr_html of response.tasks_to_render) {
                tasks_count = tasks_count + 1;
                $('#tasks_table tr:last').after(next_task_tr_html);
            }
            $('#tasks_count').text(tasks_count);
            // next_task_tr_html = response.next_task_tr;
            // if (next_task_tr_html != "") {
            //     $('#tasks_table tr:last').after(next_task_tr_html);
            // } else {
            //     $('#tasks_count').text(tasks_count - 1);
            // }
        }
    }).done(function (data) {
        console.log(data);
    });
});

$('#project_tasks_body').on('click', 'input[type="checkbox"]', function () {
    var data = {};
    data.id = $(this).attr('value');
    data.value = $(this).is(':checked') ? 1 : 0;
    tasks_count = $('#tasks_count').text();

    console.log(data);

    $.ajax({
        type: "POST",
        url: "/tasks/mark_as_done/",
        data: data,
        success: function (response) {
            task_row_str = '#tasks_row_' + data.id;
            $(task_row_str).remove();
            $('#tasks_count').text(tasks_count - 1);
        }
    }).done(function (data) {
        console.log(data);
    });
});

// Triggers when the dropdown at the end of a task line changes to choose an action
$('#tasks_body').on('change', 'select', function () {
    var data = {};
    data.value = $(this).val();
    res = data.value.split('_');
    action = res[0];
    data.id = res[1];

    if (action == 'notthisweek') {
        tasklist = 3;
    } else if (action == 'nextaction') {
        tasklist = 0;
    } else if (action == 'someday') {
        tasklist = 1;
    }

    console.log(data);

    $.ajax({
        type: "POST",
        url: "/tasks/change-tasklist/",
        data: {
            id: data.id,
            tasklist: tasklist, //NOT_THIS_WEEK
        },
        success: function (response) {
            task_row_str = '#tasks_row_' + data.id;
            $(task_row_str).remove();
        }
    }).done(function (data) {
        console.log(data);
    });
});


$('#tasks_body').on('click', 'a.postpone', function (event) {
    event.preventDefault();

    var data = {};
    href = $(this).attr('href');
    href_elems = href.split('/');
    data.id = href_elems[2];
    object_type = href_elems[1];

    $.ajax({
        type: "POST",
        url: "/tasks/" + data.id + "/postpone/",
        data: data,
        success: function (response) {
            object_row_str = '#tasks_row_' + data.id;
            $(object_row_str).remove();
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
    href_elems = href.split('/');
    data.id = href_elems[2];
    object_type = href_elems[1];

    $.ajax({
        type: "POST",
        url: "/" + object_type + "/" + data.id + "/delete/",
        data: data,
        success: function (json) {
            object_row_str = '#' + object_type + '_row_' + data.id;
            $(object_row_str).remove();
        }
    }).done(function (data) {
        console.log(data);
    });
});


$('#hide_future_tasks').click(function () {
    checked = $('#hide_future_tasks').is(':checked');
    href = window.location.href;
    href = href.substring(0, href.indexOf('?'));
    if (checked) {
        window.location.href = href + "?hide_future_tasks=true";
    } else {
        window.location.href = href;
    }
});

$('[data-toggle="tooltip"]').tooltip();

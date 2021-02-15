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
    tasks_count = $('#tasks_count').text();

    console.log(data);

    $.ajax({
        type: "POST",
        url: "/tasks/mark_as_done/",
        data: data,
        success: function (response) {
            task_row_str = '#tasks_row_' + data.id;
            $(task_row_str).remove();
            next_task_tr_html = response.next_task_tr;
            if (next_task_tr_html != "") {
                $('#tasks_table tr:last').after(next_task_tr_html);
            } else {
                $('#tasks_count').text(tasks_count - 1);
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
    alert(data.value);
    res = data.value.split('_');
    action = res[0];
    data.id = res[1];

    alert(action);
    alert(data.id);

    console.log(data);

    $.ajax({
        type: "POST",
        url: "/tasks/change-tasklist/",
        data: {
            id: data.id,
            tasklist: 3, //NOT_THIS_WEEK
        },
        success: function (response) {
            task_row_str = '#tasks_row_' + data.id;
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


$('#ideas_body').on('click', 'button', function () {
    var data = {};
    data.id = $(this).attr('value');

    console.log(data);

    $.ajax({
        type: "POST",
        url: "/votes/add/",
        data: data,
        success: function (response) {
            $('#user_avaible_votes').html(response.user_available_votes);
            $('#user_avaible_votes').effect("highlight", {color: 'green'}, 3000);
            idea_total_votes = '#idea_votes_' + data.id;
            $(idea_total_votes).html(response.idea_total_votes);
            $(idea_total_votes).effect("highlight", {color: 'green'}, 3000);
        }
    }).done(function (data) {
        console.log(data);
    });
});


$('#hide_future_tasks').click(function() {
    checked = $('#hide_future_tasks').is(':checked');
    href = window.location.href;
    href = href.substring(0, href.indexOf('?'));
    if (checked) {
        window.location.href = href + "?hide_future_tasks=true";
    } else {
        window.location.href = href;
    }
});
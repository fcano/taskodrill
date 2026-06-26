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

// ─── Mass-edit selection helpers ─────────────────────────────────────────────

function getSelectedTaskIds() {
    var ids = [];
    $('.task-select-checkbox:checked').each(function () {
        ids.push($(this).data('task-id'));
    });
    return ids;
}

function updateMassEditToolbar() {
    var ids = getSelectedTaskIds();
    var count = ids.length;
    if (count > 0) {
        $('#mass-edit-toolbar').show();
        $('#mass-edit-count').text(count + ' selected');
    } else {
        $('#mass-edit-toolbar').hide();
    }
}

function massEditRequest(payload) {
    var ids = getSelectedTaskIds();
    if (ids.length === 0) return;
    payload.task_ids = ids.join(',');
    payload.next = window.location.href;
    $.ajax({
        type: 'POST',
        url: '/tasks/mass-edit/',
        data: payload,
        success: function (response) {
            location.reload();
        },
        error: function (xhr) {
            alert('Mass edit failed: ' + xhr.responseText);
        }
    });
}

// Select-all / deselect-all
$(document).on('change', '#select-all-tasks', function () {
    var checked = $(this).is(':checked');
    $('.task-select-checkbox').prop('checked', checked);
    updateMassEditToolbar();
});

// Individual selection toggles toolbar
$('#tasks_body').on('change', '.task-select-checkbox', function () {
    var total = $('.task-select-checkbox').length;
    var checked = $('.task-select-checkbox:checked').length;
    $('#select-all-tasks').prop('indeterminate', checked > 0 && checked < total);
    $('#select-all-tasks').prop('checked', checked === total && total > 0);
    updateMassEditToolbar();
});

// Mass edit action buttons
$(document).on('click', '#mass-clear-due-date', function () {
    if (!confirm('Remove due date from all selected tasks?')) return;
    massEditRequest({ clear_due_date: '1' });
});

$(document).on('click', '#mass-clear-start-date', function () {
    if (!confirm('Remove start date from all selected tasks?')) return;
    massEditRequest({ clear_start_date: '1' });
});

$(document).on('click', '#mass-set-due-date', function () {
    var val = $('#mass-set-due-date-input').val();
    if (!val) { alert('Please pick a due date first.'); return; }
    massEditRequest({ due_date: val });
});

$(document).on('click', '#mass-set-start-date', function () {
    var val = $('#mass-set-start-date-input').val();
    if (!val) { alert('Please pick a start date first.'); return; }
    massEditRequest({ start_date: val });
});

$(document).on('click', '#mass-move-to-someday', function () {
    if (!confirm('Move selected tasks to Someday/Maybe?')) return;
    massEditRequest({ tasklist: '1' });
});

$(document).on('click', '#mass-move-to-notthisweek', function () {
    if (!confirm('Move selected tasks to Not This Week?')) return;
    massEditRequest({ tasklist: '3' });
});

$(document).on('click', '#mass-move-to-nextaction', function () {
    if (!confirm('Move selected tasks to Next Action?')) return;
    massEditRequest({ tasklist: '0' });
});

// ─── Mark-as-done button (the ✓ icon next to the selection checkbox) ──────────
$('#tasks_body').on('click', 'a.mark-done-btn', function (e) {
    e.preventDefault();
    var taskId = String($(this).data('task-id'));
    var postData = { id: taskId, value: 1 };
    if (typeof window.taskTimerCollectSessionSecondsForMarkDone === 'function') {
        var ts = window.taskTimerCollectSessionSecondsForMarkDone(taskId);
        if (ts > 0) {
            postData.timer_seconds = ts;
        }
    }
    $.ajax({
        type: 'POST',
        url: '/tasks/mark_as_done/',
        data: postData,
        success: function () {
            location.reload();
        }
    }).done(function (data) {
        console.log(data);
    });
});

$(document).on('click', '#task_detail_mark_done', function () {
    var $btn = $(this);
    var taskId = String($btn.data('task-id'));
    var postData = { id: taskId, value: 1 };
    if (typeof window.taskTimerCollectSessionSecondsForMarkDone === 'function') {
        var ts = window.taskTimerCollectSessionSecondsForMarkDone(taskId);
        if (ts > 0) {
            postData.timer_seconds = ts;
        }
    }
    $.ajax({
        type: 'POST',
        url: $btn.data('mark-done-url'),
        data: postData,
        success: function () {
            location.reload();
        }
    });
});

$('#project_tasks_body').on('click', 'input[type="checkbox"]', function () {
    var data = {};
    data.id = $(this).attr('value');
    data.value = $(this).is(':checked') ? 1 : 0;
    tasks_count = $('#tasks_count').text();
    tasks_due_date_count = parseInt($('#tasks_due_date_count').text());

    console.log(data);

    $.ajax({
        type: "POST",
        url: "/tasks/mark_as_done/",
        data: data,
        success: function (response) {
            task_row_str = '#tasks_row_' + data.id;
            $(task_row_str).remove();
            $('#tasks_count').text(tasks_count - 1);
            $('#tasks_due_date_count').text(tasks_due_date_count - 1);
        }
    }).done(function (data) {
        console.log(data);
    });
});

// Triggers when the dropdown at the end of a task line changes to choose an action
$('#tasks_body').on('click', '.move-to-tasklist .dropdown-item', function () {
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
    data.ndays = 1

    tasks_due_date_count = parseInt($('#tasks_due_date_count').text());

    $.ajax({
        type: "POST",
        url: "/tasks/" + data.id + "/postpone/" + data.ndays + "/",
        data: data,
        success: function (response) {
            object_row_str = '#tasks_row_' + data.id;
            $(object_row_str).remove();
            $('#tasks_due_date_count').text(tasks_due_date_count - 1);
        }
    }).done(function (data) {
        console.log(data);
    });
});


$('#tasks_body').on('click', 'a.postpone2', function (event) {
    event.preventDefault();
    
    var data = {};
    href = $(this).attr('href');
    href_elems = href.split('/');
    data.id = href_elems[2];
    object_type = href_elems[1];
    data.ndays = 2
    
    tasks_due_date_count = parseInt($('#tasks_due_date_count').text());
    
    $.ajax({
        type: "POST",
        url: "/tasks/" + data.id + "/postpone/" + data.ndays + "/",
        data: data,
        success: function (response) {
            object_row_str = '#tasks_row_' + data.id;
            $(object_row_str).remove();
            $('#tasks_due_date_count').text(tasks_due_date_count - 1);
        }
    }).done(function (data) {
        console.log(data);
    });
});

$('#tasks_body').on('click', 'a.postpone7', function (event) {
    event.preventDefault();
    
    var data = {};
    href = $(this).attr('href');
    href_elems = href.split('/');
    data.id = href_elems[2];
    object_type = href_elems[1];
    data.ndays = 7
    
    tasks_due_date_count = parseInt($('#tasks_due_date_count').text());
    
    $.ajax({
        type: "POST",
        url: "/tasks/" + data.id + "/postpone/" + data.ndays + "/",
        data: data,
        success: function (response) {
            object_row_str = '#tasks_row_' + data.id;
            $(object_row_str).remove();
            $('#tasks_due_date_count').text(tasks_due_date_count - 1);
        }
    }).done(function (data) {
        console.log(data);
    });
});

$('#project_tasks_body').on('click', 'a.postpone', function (event) {
    event.preventDefault();

    var data = {};
    href = $(this).attr('href');
    href_elems = href.split('/');
    data.id = href_elems[2];
    object_type = href_elems[1];
    data.ndays = 1

    tasks_due_date_count = parseInt($('#tasks_due_date_count').text());

    $.ajax({
        type: "POST",
        url: "/tasks/" + data.id + "/postpone/" + data.ndays + "/",
        data: data,
        success: function (response) {
            location.reload();
        }
    }).done(function (data) {
        console.log(data);
    });
});


$('#project_tasks_body').on('click', 'a.postpone2', function (event) {
    event.preventDefault();
    
    var data = {};
    href = $(this).attr('href');
    href_elems = href.split('/');
    data.id = href_elems[2];
    object_type = href_elems[1];
    data.ndays = 2
    
    tasks_due_date_count = parseInt($('#tasks_due_date_count').text());
    
    $.ajax({
        type: "POST",
        url: "/tasks/" + data.id + "/postpone/" + data.ndays + "/",
        data: data,
        success: function (response) {
            location.reload();
        }
    }).done(function (data) {
        console.log(data);
    });
});

$('#project_tasks_body').on('click', 'a.postpone7', function (event) {
    event.preventDefault();
    
    var data = {};
    href = $(this).attr('href');
    href_elems = href.split('/');
    data.id = href_elems[2];
    object_type = href_elems[1];
    data.ndays = 7
    
    tasks_due_date_count = parseInt($('#tasks_due_date_count').text());
    
    $.ajax({
        type: "POST",
        url: "/tasks/" + data.id + "/postpone/" + data.ndays + "/",
        data: data,
        success: function (response) {
            location.reload();
        }
    }).done(function (data) {
        console.log(data);
    });
});

$(document).on('click', 'a.mark-flexible', function (event) {
    event.preventDefault();

    var data = {};
    href = $(this).attr('href');
    href_elems = href.split('/');
    data.id = href_elems[2];

    $.ajax({
        type: "POST",
        url: "/tasks/" + data.id + "/mark_flexible/",
        data: data,
        success: function (json) {
            window.location.reload();
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

    tasks_due_date_count = parseInt($('#tasks_due_date_count').text());

    $.ajax({
        type: "POST",
        url: "/" + object_type + "/" + data.id + "/delete/",
        data: data,
        success: function (json) {
            object_row_str = '#' + object_type + '_row_' + data.id;
            $(object_row_str).remove();
            $('#tasks_due_date_count').text(tasks_due_date_count - 1);
        }
    }).done(function (data) {
        console.log(data);
    });
});


$(document).on('click', 'a.remove-deadline-prio', function (event) {
    event.preventDefault();

    var data = {};
    href = $(this).attr('href');
    href_elems = href.split('/');
    data.id = href_elems[2];
    object_type = href_elems[1];

    $.ajax({
        type: "POST",
        url: "/" + object_type + "/" + data.id + "/remove_deadline_prio/",
        data: data,
        success: function (json) {
            /* If the result is to reload the page, AJAX is not needed */
            /* Pending: remove AJAX */
            window.location.reload();
        }
    }).done(function (data) {
        console.log(data);
    });
});


$(document).on('click', 'a.remove-deadline', function (event) {
    event.preventDefault();

    var data = {};
    href = $(this).attr('href');
    href_elems = href.split('/');
    data.id = href_elems[2];
    object_type = href_elems[1];

    $.ajax({
        type: "POST",
        url: "/" + object_type + "/" + data.id + "/remove_deadline/",
        data: data,
        success: function (json) {
            /* If the result is to reload the page, AJAX is not needed */
            /* Pending: remove AJAX */
            window.location.reload();
        }
    }).done(function (data) {
        console.log(data);
    });
});





function refreshWithParams() {
    var href = window.location.href;
    var qIndex = href.indexOf('?');
    if (qIndex !== -1) {
        href = href.substring(0, qIndex);
    }
    var params = [];
    if ($('#hide_future_tasks').is(':checked')) {
        params.push('hide_future_tasks=true');
    }
    if ($('#show_done_tasks').is(':checked')) {
        params.push('show_done_tasks=true');
    }
    if (params.length > 0) {
        window.location.href = href + '?' + params.join('&');
    } else {
        window.location.href = href;
    }
}

$('#hide_future_tasks').click(function () {
    refreshWithParams();
});

$('#show_done_tasks').click(function () {
    refreshWithParams();
});

$('.js-autocomplete-filter').each(function() {
    var $input = $(this);
    var $hidden = $($input.data('hidden'));
    var items = JSON.parse($input.attr('data-items'));

    $input.autocomplete({
        source: function(request, response) {
            var term = request.term.toLowerCase();
            var matches = items.filter(function(item) {
                return item.label.toLowerCase().indexOf(term) !== -1;
            });
            response(matches);
        },
        select: function(event, ui) {
            $hidden.val(ui.item.value);
            $(this).val(ui.item.label);
            return false;
        },
        focus: function(event, ui) {
            $(this).val(ui.item.label);
            return false;
        },
        minLength: 0
    }).on('input', function() {
        if ($(this).val() === '') {
            $hidden.val('');
        }
    }).on('focus', function() {
        if ($(this).val() === '') {
            $(this).autocomplete('search', '');
        }
    });
});

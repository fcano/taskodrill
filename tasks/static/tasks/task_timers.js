(function ($) {
    'use strict';

    if (!window.TASK_TIMER_URLS || !$('.task-timer-cell').length) {
        return;
    }

    var pendingTaskId = null;

    function pad2(n) {
        return (n < 10 ? '0' : '') + n;
    }

    function formatSessionMs(ms) {
        var s = Math.floor(ms / 1000);
        var h = Math.floor(s / 3600);
        var m = Math.floor((s % 3600) / 60);
        var sec = s % 60;
        if (h > 0) {
            return h + ':' + pad2(m) + ':' + pad2(sec);
        }
        return m + ':' + pad2(sec);
    }

    function formatTotalSeconds(sec) {
        sec = parseInt(sec, 10) || 0;
        return formatSessionMs(sec * 1000);
    }

    function parseIsoToMs(iso) {
        if (!iso) {
            return null;
        }
        var t = Date.parse(iso);
        return isNaN(t) ? null : t;
    }

    function getState($cell) {
        var st = $cell.data('timerState');
        if (!st) {
            st = { accumulatedMs: 0, intervalId: null, running: false, segmentStartMs: null };
            $cell.data('timerState', st);
        }
        return st;
    }

    function clearTick($cell) {
        var st = getState($cell);
        if (st.intervalId) {
            clearInterval(st.intervalId);
            st.intervalId = null;
        }
    }

    function currentElapsedMs($cell) {
        var st = getState($cell);
        var extra = 0;
        if (st.running && st.segmentStartMs != null) {
            extra = Date.now() - st.segmentStartMs;
        }
        return st.accumulatedMs + extra;
    }

    function updateDisplay($cell) {
        $cell.find('.task-timer-display').text(formatSessionMs(currentElapsedMs($cell)));
    }

    function syncButtons($cell) {
        var st = getState($cell);
        var hasAccum = st.accumulatedMs > 0 || st.running;
        $cell.find('.task-timer-play').prop('disabled', st.running);
        $cell.find('.task-timer-pause').prop('disabled', !st.running);
        $cell.find('.task-timer-stop').prop('disabled', !hasAccum);
    }

    function setCellServerSnapshot($cell, accumulatedSeconds, segmentStartedAtIso) {
        $cell.attr('data-timer-accumulated', String(accumulatedSeconds || 0));
        if (segmentStartedAtIso) {
            $cell.attr('data-timer-segment-start', segmentStartedAtIso);
        } else {
            $cell.removeAttr('data-timer-segment-start');
        }
    }

    function applyServerSnapshot($cell, accumulatedSeconds, segmentStartedAtIso) {
        clearTick($cell);
        var st = getState($cell);
        st.accumulatedMs = (parseInt(accumulatedSeconds, 10) || 0) * 1000;
        var segMs = parseIsoToMs(segmentStartedAtIso);
        st.running = segMs != null;
        st.segmentStartMs = segMs;
        setCellServerSnapshot($cell, accumulatedSeconds, segmentStartedAtIso);
        if (st.running) {
            st.intervalId = setInterval(function () {
                updateDisplay($cell);
            }, 250);
        }
        updateDisplay($cell);
        syncButtons($cell);
    }

    function hasFolder($cell) {
        var id = $cell.attr('data-folder-id');
        return id !== undefined && id !== null && String(id).trim() !== '';
    }

    function postJson(url, payload, onSuccess) {
        $.ajax({
            type: 'POST',
            url: url,
            contentType: 'application/json; charset=utf-8',
            data: JSON.stringify(payload),
            success: onSuccess
        });
    }

    function initCellFromDom($cell) {
        var acc = parseInt($cell.attr('data-timer-accumulated'), 10) || 0;
        var segIso = $cell.attr('data-timer-segment-start');
        applyServerSnapshot($cell, acc, segIso || null);
    }

    function playTimerForCell($cell) {
        var taskId = $cell.data('task-id');
        postJson(window.TASK_TIMER_URLS.timerPlay, { task_id: taskId }, function (res) {
            if (res && res.ok) {
                applyServerSnapshot(
                    $cell,
                    res.accumulated_seconds,
                    res.segment_started_at
                );
            }
        });
    }

    function pauseTimerForCell($cell) {
        var taskId = $cell.data('task-id');
        postJson(window.TASK_TIMER_URLS.timerPause, { task_id: taskId }, function (res) {
            if (res && res.ok) {
                applyServerSnapshot($cell, res.accumulated_seconds, null);
            }
        });
    }

    function formatTotalDisplay($cell) {
        var $tot = $cell.find('.task-timer-total-value');
        var sec = parseInt($tot.attr('data-seconds'), 10) || 0;
        $tot.text(formatTotalSeconds(sec));
    }

    function stopTimerForCell($cell) {
        var taskId = $cell.data('task-id');
        postJson(window.TASK_TIMER_URLS.logTime, { task_id: taskId, seconds: 0 }, function (res) {
            if (res && res.ok) {
                applyServerSnapshot($cell, 0, null);
                if (res.tracked_time_seconds != null) {
                    var $tot = $cell.find('.task-timer-total-value');
                    $tot.attr('data-seconds', res.tracked_time_seconds);
                    formatTotalDisplay($cell);
                }
            }
        });
    }

    $('.task-timer-cell').each(function () {
        var $c = $(this);
        formatTotalDisplay($c);
        initCellFromDom($c);
    });

    $('#tasks_body').on('click', '.task-timer-play', function () {
        var $cell = $(this).closest('.task-timer-cell');
        var st = getState($cell);
        if (st.running) {
            return;
        }
        if (!hasFolder($cell)) {
            pendingTaskId = $cell.data('task-id');
            $('#folderPickerModalInput').val('');
            $('#folderPickerModal').modal('show');
            return;
        }
        playTimerForCell($cell);
    });

    $('#tasks_body').on('click', '.task-timer-pause', function () {
        pauseTimerForCell($(this).closest('.task-timer-cell'));
    });

    $('#tasks_body').on('click', '.task-timer-stop', function () {
        stopTimerForCell($(this).closest('.task-timer-cell'));
    });

    $('#folderPickerModalConfirm').on('click', function () {
        if (!pendingTaskId) {
            return;
        }
        var name = $('#folderPickerModalInput').val().trim();
        if (!name) {
            return;
        }
        var $cell = $('.task-timer-cell[data-task-id="' + pendingTaskId + '"]');
        $.ajax({
            type: 'POST',
            url: window.TASK_TIMER_URLS.assignFolder,
            contentType: 'application/json; charset=utf-8',
            data: JSON.stringify({
                task_id: pendingTaskId,
                folder_name: name
            }),
            success: function (res) {
                if (res && res.folder_id) {
                    $cell.attr('data-folder-id', res.folder_id);
                }
                $('#folderPickerModal').modal('hide');
                pendingTaskId = null;
                playTimerForCell($cell);
            }
        });
    });

    $('#folderPickerModal').on('hidden.bs.modal', function () {
        pendingTaskId = null;
    });

    $('#folderPickerModalInput').autocomplete({
        minLength: 0,
        source: function (request, response) {
            $.getJSON(window.TASK_TIMER_URLS.folderSuggest, { term: request.term }, response);
        },
        select: function (event, ui) {
            $('#folderPickerModalInput').val(ui.item.value);
            return false;
        }
    });

    /**
     * Unsaved client-only seconds (for mark-as-done when no server session).
     * With server-backed timers, mark_as_done drains the session; this returns 0 if in sync.
     */
    window.taskTimerCollectSessionSecondsForMarkDone = function (taskId) {
        var $cell = $('.task-timer-cell[data-task-id="' + taskId + '"]');
        if (!$cell.length) {
            return 0;
        }
        var st = getState($cell);
        if (st.running && st.segmentStartMs != null) {
            st.accumulatedMs += Date.now() - st.segmentStartMs;
        }
        st.segmentStartMs = null;
        st.running = false;
        if (st.intervalId) {
            clearInterval(st.intervalId);
            st.intervalId = null;
        }
        var secs = Math.max(0, Math.floor(st.accumulatedMs / 1000));
        st.accumulatedMs = 0;
        updateDisplay($cell);
        syncButtons($cell);
        return secs;
    };
})($);

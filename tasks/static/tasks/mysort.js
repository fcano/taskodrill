const groups = document.getElementById('project_tasks_body');
let sortable = Sortable.create(groups, {
    handle: '.handle',
});

const saveOrderingButton = document.getElementById('saveOrdering');
const orderingForm = document.getElementById('orderingForm');
const formInput = orderingForm.querySelector('#orderingInput');

function saveOrdering() {
    const rows = document.getElementById("project_tasks_body").querySelectorAll('tr');
    let ids = [];
    for (let row of rows) {
        ids.push(row.dataset.lookup);
    }
    formInput.value = ids.join(',');
    orderingForm.submit();
}

saveOrderingButton.addEventListener('click', saveOrdering);

const sortByDueDateButton = document.getElementById('sortByDueDate');
if (sortByDueDateButton) {
    sortByDueDateButton.addEventListener('click', function () {
        const tbody = document.getElementById('project_tasks_body');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        rows.sort(function (a, b) {
            const dateA = a.dataset.dueDate || '9999-12-31';
            const dateB = b.dataset.dueDate || '9999-12-31';
            return dateA.localeCompare(dateB);
        });
        rows.forEach(function (row) {
            tbody.appendChild(row);
        });
        saveOrdering();
    });
}
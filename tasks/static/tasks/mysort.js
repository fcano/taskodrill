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
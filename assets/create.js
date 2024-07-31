// Markdown Preview
if ($ === undefined) $ = CTFd.lib.$
$('#desc-edit').on('shown.bs.tab', function(event) {
    if (event.target.hash == '#desc-preview') {
        var editor_value = $('#desc-editor').val();
        $(event.target.hash).html(
            CTFd._internal.challenge.render(editor_value)
        );
    }
});
$('#new-desc-edit').on('shown.bs.tab', function(event) {
    if (event.target.hash == '#new-desc-preview') {
        var editor_value = $('#new-desc-editor').val();
        $(event.target.hash).html(
            CTFd._internal.challenge.render(editor_value)
        );
    }
});
$("#solve-attempts-checkbox").change(function() {
    if (this.checked) {
        $('#solve-attempts-input').show();
    } else {
        $('#solve-attempts-input').hide();
        $('#max_attempts').val('');
    }
});

$(document).ready(function() {
    $('[data-toggle="tooltip"]').tooltip();
});

const flagTypeSelect = document.querySelector('select[name="flag_type"]');
const flagFileFields = document.querySelectorAll('.flag-file');

// Function to toggle visibility based on selected flag type
function toggleFlagFields() {
    if (flagTypeSelect.value == "0") { // "File" selected
        flagFileFields.forEach(field => field.style.display = 'block');
    } else { // "Environment Variable" selected
        flagFileFields.forEach(field => field.style.display = 'none');
    }
}

// Initial check to set the correct visibility on page load
toggleFlagFields();

// Add event listener to the select element to toggle visibility on change
flagTypeSelect.addEventListener('change', toggleFlagFields);

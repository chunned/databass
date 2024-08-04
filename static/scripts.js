document.addEventListener('DOMContentLoaded', function() {
    let deleteButton = document.querySelector("#delete");
    deleteButton.addEventListener("click", function() {
        showPopup(deleteButton);
    });
});


function showPopup(deleteButton) {
    let releaseId = deleteButton.getAttribute('data-id');
    const popup = document.createElement('div');
    popup.className = 'popup';
    popup.innerHTML = `
    <p>Are you sure? This cannot be undone.</p>
    <button id="confirm" class="search-btn">yes</button>
    <button id="cancel" class="search-btn">no</button>
    `;
    document.body.appendChild(popup);
    // If 'yes' button is pressed, delete the release
    popup.querySelector('#confirm').addEventListener('click', function() {
        fetch('/delete', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ id: releaseId })
        })
        .then(response => {
            window.location.href = response.url;
        })
    });
    popup.querySelector('#cancel').addEventListener('click', function() {
        document.body.removeChild(popup);
    });
}
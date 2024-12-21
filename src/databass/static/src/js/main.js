function handleDeleteButton(deleteButton) {
    let itemId = deleteButton.getAttribute('data-id');
    let itemType = deleteButton.getAttribute('data-type');
    const popup = document.createElement('div');
    popup.className = 'popup';
    popup.id = 'delete_popup';
    popup.innerHTML = `
    <h1>Are you sure?&nbsp;This cannot be undone.</h1>
    <div>
    <button id="confirm" class="delete">delete</button>
    <button id="cancel" class="delete">cancel</button>
    </div>
    `;
    document.body.appendChild(popup);
    // If 'yes' button is pressed, delete the release
    popup.querySelector('#confirm').addEventListener('click', function() {
        fetch('/delete', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ id: itemId, type: itemType })
        })
        .then(response => {
            window.location.href = response.url;
        })
    });
    popup.querySelector('#cancel').addEventListener('click', function() {
        document.body.removeChild(popup);
    });
}

function handleEditButton(editButton) {
    let releaseId = editButton.getAttribute('data-id');
    fetch('/release/' + releaseId + '/edit')
        .then(response => response.text())
        .then(html => {
            let popup = document.createElement('div');
            popup.id = 'edit_popup';
            popup.className = 'popup';
            popup.innerHTML = html;
            document.body.appendChild(popup);

            popup.querySelector('#edit_cancel').addEventListener('click', () => {
                document.body.removeChild(popup);
            });
        })
}

function formatDataString(data) {
    // Escape parts of response data that cause JSON.parse to error
    // Some of these are extremely case specific; ideally should be more generalized
    // i.e
    // .replace(/ "n/g, " 'n") = Drum "n' Bass -> Drum 'n' Bass
    // .replace(/ "n' /g, " 'n' ") = Neu! "75 -> Neu! '75
    // Both of the above cases are caused by the other more generic replacements
    // Way to avoid most of this altogether would be to just URLencode key/value pairs
    return data
        .replace(/{'/g, '{"')
        .replace(/'}/g, '"}')
        .replace(/':/g, '":')
        .replace(/ '/g, ' "')
        .replace(/',/g, '",')
        .replace(/ "n' /g, " 'n' ")
        .replace(/\['/g, '\["')
        .replace(/'\]/g, '"\]')
        .replace(/! "75/g, "! '75'")
        .replace(/(12|10|7)" Vinyl/g, '$1\\" Vinyl');
}


function addPopupListeners(html) {
    document.querySelector("#search_results").innerHTML = html;
    let tableRows = document.querySelectorAll(".row");
    tableRows.forEach((tableRow) => {
        tableRow.addEventListener("click", function() {
            let data = formatDataString(tableRow.dataset.item);
            let parsed_data = JSON.parse(data)
            fetch("/new_release", {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(parsed_data)
            })
                .then(response => response.text())
                .then(html => {
                    let popup = document.createElement('div')
                    popup.className = 'popup';
                    popup.innerHTML = html;
                    document.body.appendChild(popup);
                    popup.querySelector('.close-btn').addEventListener('click', function() {
                        document.body.removeChild(popup);
                    });
                })
                .catch(err => { console.log(err) })
        });
    });
}

function handleSearchButton() {
    let page;
    try {
        page = document.querySelector('#current_page').value;
    } catch(e) {
        page = "1";
    }
    let referrer;
    try {
        referrer = document.querySelector("#referrer").value;
    } catch(e) {
        referrer = "search"
    }
    const data = {
        release: document.querySelector("#release").value,
        artist: document.querySelector("#artist").value,
        label: document.querySelector("#label").value,
        "referrer": referrer,
        "page": page
    };
    fetch('/search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.text())
    .then(html => {
        // add event listener to each table row
        addPopupListeners(html);
    })
    .catch(error => {
        console.error('Fetch error:', error);
    });
}

function handleSearchPageButton(direction) {
    // Retrieve next page and per_page numbers as integer
    let next = getPageButtonDirection(direction);
    let perPage = +document.querySelector("#per_page").innerHTML;
    // Retrieve raw data list and parse it as JSON
    let data = document.querySelector("#data_full").innerHTML;
    let formatted = formatDataString(data);
    let parsed = JSON.parse(formatted);
    let requestData = {
        "next_page": next,
        "per_page": perPage,
        "data": parsed,
        "referrer": "page_button"
    }
    fetch('/search', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(requestData)
    })
    .then(response => response.text())
    .then(html => {addPopupListeners(html)})
}

function getPageButtonDirection(direction) {
    let next;
    if (direction === 'next') {
        next = +document.querySelector("#next_page").value;
    } else if (direction === 'prev') {
        next = +document.querySelector("#prev_page").value;
    }
    return next;
}

// function handleStatsSearch() {
//     let data = document.getElementById("stats-filter")
//     let vars = data.querySelectorAll("select");
//
//     let formData = {};
//     vars.forEach(input => {
//         formData[input.name] = input.value;
//     });
//     Object.keys(formData).forEach(key => {
//         if (formData[key] === '') {
//             let alertStr = `Empty form field: ${key}`
//             alert(alertStr);
//         }
//     });
//     fetch('/stats_search', {
//         method: 'GET',
//         headers: {'Content-Type': 'application/json'},
//         body: JSON.stringify(formData)
//     })
// }

function loadHomeTable(direction) {
    let currentPage;
    try {
        currentPage = document.getElementById('current_page').value;
    } catch (e) {
        currentPage = "1";
    }
    let targetPage = currentPage;
    if (direction === 'prev') targetPage = parseInt(currentPage) - 1;
    if (direction === 'next') targetPage = parseInt(currentPage) + 1;

    fetch('/home_release_table?page=' + targetPage)
        .then(response => response.text())
        .then(html => {
            document.getElementById('home_release_table').innerHTML = html;
        });
}

function loadSearchTable(type, direction) {
    let formData;
    if (type === 'release') {
        formData = {
            name: document.querySelector("#name").value,
            artist: document.querySelector("#artist").value,
            label: document.querySelector("#label").value,
            country: document.querySelector("#country").value,
            rating_comparison: document.querySelector("#rating-filter").value,
            rating: document.querySelector("#rating").value,
            year_comparison: document.querySelector("#year-filter").value,
            year: document.querySelector("#year").value,
            main_genre: document.querySelector("#main_genre").value,
            // genres: [document.querySelector("#genres").value]
        };
        console.log(formData);
    }
    if (type === 'artist') {
        formData = {
            name: document.querySelector("#artist").value,
            country: document.querySelector("#country").value,
            begin_comparison: document.querySelector("#begin_filter").value,
            begin_date: document.querySelector("#begin").value,
            end_comparison: document.querySelector("#end_filter").value,
            end_date: document.querySelector("#end").value,
            type: document.querySelector("#type").value
        };
    }
    if (type === 'label') {
        formData = {
            name: document.querySelector("#label").value,
            country: document.querySelector("#country").value,
            begin_comparison: document.querySelector("#begin_filter").value,
            begin_date: document.querySelector("#begin").value,
            end_comparison: document.querySelector("#end_filter").value,
            end_date: document.querySelector("#end").value,
            type: document.querySelector("#type").value,
        }
    }
    let currentPage;
    try {
        currentPage = document.getElementById('current_page').value;
    } catch(e) {
        currentPage = "1";
    }
    let targetPage = currentPage;
    if (direction === 'prev') targetPage = parseInt(currentPage) - 1;
    if (direction === 'next') targetPage = parseInt(currentPage) + 1;
    fetch('/' + type + '_search?page=' + targetPage, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(formData)
    })
        .then(response => response.text())
        .then(html => {
            document.getElementById('search-results').innerHTML = html;
        })
}

document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname === "/" || window.location.pathname === "/home") {
        loadHomeTable();
        document.addEventListener('click', function(event) {
            if (event.target.classList.contains('prev_page')) {
                loadHomeTable('prev')
            }
            if (event.target.classList.contains('next_page')) {
                loadHomeTable('next')
            }
        });
    }

    if (window.location.pathname === "/new") {
        document.addEventListener('click', function(event) {
            if (event.target && event.target.classList.contains('manual-entry')) {
                fetch('/search', {
                    method: 'GET'
                })
                    .then(response => response.text())
                    .then(html => {
            document.getElementById('search_results').innerHTML = html;
                    })
                    .catch(error => {
                        console.error('Fetch error:', error);
                    });
            }
            if (event.target && event.target.classList.contains('new-release-search')) {
                handleSearchButton();
            }
            if (event.target && event.target.classList.contains('page-btn')) {
                let direction = event.target.dataset.direction;
                handleSearchPageButton(direction);
            }
        });
        document.addEventListener('keydown', function (event) {
            if (event.key === 'Enter') {
                handleSearchButton();
            }
        });
    }

    if (window.location.pathname === "/releases") {
        document.addEventListener('click', function (event) {
            if (event.target && event.target.id === 'release-search') {
                loadSearchTable('release');
            }
            if (event.target && event.target.classList.contains('pagination_button')) {
                if (event.target.classList.contains('prev_page')) {
                    loadSearchTable('release', 'prev')
                }
                if (event.target.classList.contains('next_page')) {
                    loadSearchTable('release', 'next')
                }
            }
        })
    }

    if (window.location.pathname === "/artists") {
        document.addEventListener('click', function (event) {
            if (event.target && event.target.id === 'artist-search') {
                loadSearchTable('artist');
            }
            if (event.target && event.target.classList.contains('pagination_button')) {
                if (event.target.classList.contains('prev_page')) {
                    loadSearchTable('artist', 'prev')
                }
                if (event.target.classList.contains('next_page')) {
                    loadSearchTable('artist', 'next')
                }
            }
        })
    }

    if (window.location.pathname === "/labels") {
        document.addEventListener('click', function (event) {
            if (event.target && event.target.id === 'label-search') {
                loadSearchTable('label');
            }
            if (event.target && event.target.classList.contains('pagination_button')) {
                if (event.target.classList.contains('prev_page')) {
                    loadSearchTable('label', 'prev')
                }
                if (event.target.classList.contains('next_page')) {
                    loadSearchTable('label', 'next')
                }
            }
        })
    }

    document.addEventListener('click', function(event) {
        if (event.target && event.target.classList.contains('delete-btn')) {
            let deleteBtn = document.querySelector("#delete-btn");
            handleDeleteButton(deleteBtn);
        }

        if (event.target && event.target.id === 'edit-btn') {
            let editButton = document.querySelector('#edit-btn');
            handleEditButton(editButton);
        }

        // if (event.target && event.target.classList.contains('stats-search')) {
        //     handleStatsSearch();
        // }
    });
});



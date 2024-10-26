function handleDeleteButton(deleteButton) {
    let itemId = deleteButton.getAttribute('data-id');
    let itemType = deleteButton.getAttribute('data-type');
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

function popupHTML(parsed_data) {
    console.log(parsed_data);
    return `
    <div class="popup-content">
        <span class="close-btn">&times;</span>
        <form action="/submit" method="POST" id="popup-form">
            <input type="hidden" name="manual_submit" value="false">
            <input type="hidden" name="release_group_id" value="${parsed_data.release_group_id}">
            <input type="hidden" name="release_name" value="${parsed_data.release.name}">
            <input type="hidden" name="artist" value="${parsed_data.artist.name}">
            <input type="hidden" name="label" value="${parsed_data.label.name}">
            <input type="hidden" name="release_mbid" value="${parsed_data.release.mbid}">
            <input type="hidden" name="artist_mbid" value="${parsed_data.artist.mbid}">
            <input type="hidden" name="label_mbid" value="${parsed_data.label.mbid}">
            <input type="hidden" name="track_count" value="${parsed_data.track_count}">
            <input type="hidden" name="country" value="${parsed_data.country}">
            <table id="popup-table">
                <tr>
                    <td>RELEASE</td>
                    <td>${parsed_data.release.name}</td>
                </tr>
                <tr>
                    <td>ARTIST</td>
                    <td>${parsed_data.artist.name}</td>
                </tr>
                </tr>
                <tr>
                    <td>LABEL</td>
                    <td>${parsed_data.label.name}</td>
                </tr>
                <tr>
                    <td>TRACKS</td>
                    <td>${parsed_data["track_count"]}</td>
                </tr>
                <tr>
                    <td>
                        <label for="rating">RATING</label>
                    </td>
                    <td>
                        <input type="number" min="0" max="100" required id="rating" name="rating">
                    </td>
                </tr>
                <tr>
                    <td>
                        <label for="release_year">YEAR</label>
                    </td>
                    <td>
                        <input type="number" min="0" required id="year" name="release_year" value="${parsed_data.date}">
                    </td>
                </tr>
                <tr>
                    <td>
                        <label for="genre">GENRE</label>
                    </td>
                    <td>
                        <input type="text" required id="genre" name="genre">
                    </td>
                </tr>
                <tr>
                    <td>
                        <label for="tags">TAGS</label>
                    </td>
                    <td>
                        <input type="text" id="tags" name="tags">
                    </td>
                </tr>
                <tr>
                    <td colspan="2">
                        <button type="submit" id="submit-btn" class="search-submit-btn">submit</button>
                    </td>
                </tr>
            </table>
        </form>
    </div>
    `;
}

function searchPopup(data) {
    // Used in static.html to show popup before release is inserted
    try {
        let jsonStr = formatDataString(data);
        try {
            const parsed_data = JSON.parse(jsonStr) // Create the pop-up container
            const popup = document.createElement('div');
            popup.className = 'popup';
            popup.innerHTML = popupHTML(parsed_data)
            // Append the pop-up to the body
            document.body.appendChild(popup);
            // Close the pop-up when the close button is clicked
            popup.querySelector('.close-btn').addEventListener('click', function() {
                document.body.removeChild(popup);
            });
        } catch (error) {
            console.error(error);
            console.log(jsonStr);
        }
    } catch (error) {
        console.error('Failed to parse data-item:', error);
    }
}

function handleSearchSubmitButton() {
    let form = document.getElementById("popup-form");
    let form_data = {};
    let inputs = form.querySelectorAll('input');
    inputs.forEach(function(input) {
        form_data[input.name] = input.value;
    })
    form_data['manual_submit'] = 'false';
    fetch('/image_search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(form_data)
    })
    .then(response => {
        if (response.ok) {
            return response.text()
        } else {
            throw new Error('Failed to submit form')
        }
    })
}

function addPopupListeners(html) {
    document.querySelector("#search-results").innerHTML = html;
    let tableRows = document.querySelectorAll("#data-form table tbody tr");
    tableRows.forEach((tableRow) => {
        tableRow.addEventListener("click", function() {
            let data = tableRow.dataset.item;
            searchPopup(data);
        });
    });
}

function handleSearchButton() {
    const data = {
        release: document.querySelector("#release").value,
        artist: document.querySelector("#artist").value,
        label: document.querySelector("#label").value,
        "referrer": "search"
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
        addPopupListeners(html);
    })
    .catch(error => {
        console.error('Fetch error:', error);
    });
}

function handlePageButton(direction) {
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

function handleDynamicPageButton(direction) {
    let next = getPageButtonDirection(direction);
    let perPage = +document.querySelector("#per_page").innerHTML;
    let data = document.querySelector("#data_full").innerHTML;
    let search_type = document.querySelector("#search_type").innerHTML;
    let formatted = formatDataString(data);
    let parsed = JSON.parse(formatted);
    let requestData = {"next_page": next, "per_page": perPage, "data": parsed, "referrer": "page_button", "search_type": search_type}
     fetch('/dynamic_search', {
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

function handleReleaseSearch() {
    let data = {
        name: document.querySelector("#name").value,
        artist: document.querySelector("#artist").value,
        label: document.querySelector("#label").value,
        country: document.querySelector("#country").value,
        rating_comparison: document.querySelector("#rating-filter").value,
        rating: document.querySelector("#rating").value,
        year_comparison: document.querySelector("#year-filter").value,
        release_year: document.querySelector("#release_year").value,
        genre: document.querySelector("#genre").value,
        tags: [document.querySelector("#tags").value]
    };
    fetch('/release_search', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    })
    .then(function(response) {
        return response.text();
    })
    .then(function(html) {
        document.querySelector("#search-results").innerHTML = html;
    })
}

function handleArtistSearch() {
    let data = {
        name: document.querySelector("#artist").value,
        country: document.querySelector("#country").value,
        begin_comparison: document.querySelector("#begin_filter").value,
        begin_date: document.querySelector("#begin_date").value,
        end_comparison: document.querySelector("#end_filter").value,
        end_date: document.querySelector("#end_date").value,
        type: document.querySelector("#type").value
    };
    fetch('/artist_search', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    })
        .then(function(response) {
            return response.text();
        })
        .then(function(html) {
            document.querySelector("#search-results").innerHTML = html;
        })
}

function handleLabelSearch() {
    let data = {
        name: document.querySelector("#label").value,
        country: document.querySelector("#country").value,
        begin_comparison: document.querySelector("#begin_filter").value,
        begin_date: document.querySelector("#begin_date").value,
        end_comparison: document.querySelector("#end_filter").value,
        end_date: document.querySelector("#end_date").value,
        type: document.querySelector("#type").value,
    }
    fetch('/label_search', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    })
    .then(function(response) {
        return response.text();
    })
    .then(function(html) {
        document.querySelector("#search-results").innerHTML = html;
    })
}

function handleStatsSearch() {
    let data = document.getElementById("stats-filter")
    let vars = data.querySelectorAll("select");

    let formData = {};
    vars.forEach(input => {
        formData[input.name] = input.value;
    });
    Object.keys(formData).forEach(key => {
        if (formData[key] === '') {
            let alertStr = `Empty form field: ${key}`
            alert(alertStr);
        }
    });
    fetch('/stats_search', {
        method: 'GET',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(formData)
    })
}


document.addEventListener('DOMContentLoaded', () => {
    document.addEventListener('click', function(event) {
        // Handle search button click
        if (event.target && event.target.classList.contains('new-release-search')) {
            handleSearchButton();
        }
       if (event.target && event.target.classList.contains('search-submit-btn')) {
           handleSearchSubmitButton();
       }
        if (event.target && event.target.classList.contains('delete-btn')) {
            let deleteBtn = document.querySelector("#delete-btn");
            handleDeleteButton(deleteBtn);
        }
        // Handle /search pagination button clicks
        if (event.target && event.target.classList.contains('page-btn')) {
            let direction = event.target.dataset.direction;
            handlePageButton(direction);
        }
        if (event.target && event.target.classList.contains('release-search')) {
            handleReleaseSearch();
        }
        if (event.target && event.target.classList.contains('artist-search')) {
            handleArtistSearch();
        }
        if (event.target && event.target.classList.contains('label-search')) {
            handleLabelSearch();
        }
        // Handle /releases, /labels, /artists pagination button clicks
        if (event.target && event.target.classList.contains('dynamic-page-btn')) {
            let direction = event.target.dataset.direction;
            handleDynamicPageButton(direction);
        }
        // Handle /stats search button
        if (event.target && event.target.classList.contains('stats-search')) {
            handleStatsSearch();
        }
    });
    if (document.querySelector('#new-release')) {
        document.addEventListener('keydown', function (event) {
            if (event.key === 'Enter') {
                handleSearchButton();
            }
        })
    }
});



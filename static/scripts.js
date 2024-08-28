function handleDeleteButton(deleteButton) {
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
            console.log(response);
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
        .replace(/! "75/g, "! '75'")
        .replace(/(12|10|7)" Vinyl/g, '$1\\" Vinyl');
}


function popupHTML(parsed_data) {
    return `
    <div class="popup-content">
        <span class="close-btn">&times;</span>
        <form action="/submit" method="POST" id="popup-form">
            <input type="hidden" name="release" value="${parsed_data.release.name}">
            <input type="hidden" name="artist" value="${parsed_data.artist.name}">
            <input type="hidden" name="label" value="${parsed_data.label.name}">
            <input type="hidden" name="release_mbid" value="${parsed_data.release.mbid}">
            <input type="hidden" name="artist_mbid" value="${parsed_data.artist.mbid}">
            <input type="hidden" name="label_mbid" value="${parsed_data.label.mbid}">
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
                    <td>${parsed_data["track-count"]}</td>
                </tr>
                <tr>
                    <td>
                        <label for="rating">RATING</label>
                    </td>
                    <td>
                        <input type="number" min="0" max="100" required id="rating" name="rating" class="search-btn">
                    </td>
                </tr>
                <tr>
                    <td>
                        <label for="release_year">YEAR</label>
                    </td>
                    <td>
                        <input type="number" min="0" required id="year" name="release_year" class="search-btn" value="${parsed_data.date}">
                    </td>
                </tr>
                <tr>
                    <td>
                        <label for="genre">GENRE</label>
                    </td>
                    <td>
                        <input type="text" required id="genre" name="genre" class="search-btn">
                    </td>
                </tr>
                <tr>
                    <td>
                        <label for="tags">TAGS</label>
                    </td>
                    <td>
                        <input type="text" id="tags" name="tags" class="search-btn">
                    </td>
                </tr>
                <tr>
                    <td colspan="2">
                        <button type="submit" id="submit-btn" class="search-btn">submit</button>
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
            console.log(parsed_data);
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
        console.log(data-item)
    }
}

function updateSearchPage(new_data) {
    let searchTableBody = document.getElementById('paged_search');
    searchTableBody.innerHTML = ''; // Clear existing rows

    new_data.forEach(item => {
        const row = document.createElement('tr');
        row.classList.add('search-data');
        row.dataset.item = JSON.stringify(item);

        row.innerHTML = `
            <td style="display: none;">
                <input value="${JSON.stringify(item)}" type="radio" name="selected_item">
            </td>
            <td class="long">${item.release.name}</td>
            <td class="long">${item.artist.name}</td>
            <td class="long">${item.label.name}</td>
            <td class="short">${item.date}</td>
            <td class="short">${item.trackCount}</td>
            <td class="long">${item.format}</td>
            <td style="display: none;">${item.releaseYear}</td>
            <td style="display: none;">${item.rating}</td>
            <td style="display: none;">${item.genre}</td>
            <td style="display: none;">${item.tags}</td>
        `;

        searchTableBody.appendChild(row);
    });

    // Add popup listeners to the new rows
    addPopupListeners();
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
    perPage = +document.querySelector("#per_page").innerHTML;
    // Retrieve raw data list and parse it as JSON
    data = document.querySelector("#data_full").innerHTML;
    formatted = formatDataString(data);
    parsed = JSON.parse(formatted);
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
    perPage = +document.querySelector("#per_page").innerHTML;
    data = document.querySelector("#data_full").innerHTML;
    search_type = document.querySelector("#search_type").innerHTML;
    formatted = formatDataString(data);
    parsed = JSON.parse(formatted);
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
        qtype: "release",
        referrer: "release",
        name: document.querySelector("#name").value,
        artist: document.querySelector("#artist").value,
        label: document.querySelector("#label").value,
        country: document.querySelector("#country").value,
        rating_comparison: document.querySelector("#rating-filter").value,
        rating: document.querySelector("#rating").value,
        year_comparison: document.querySelector("#year-filter").value,
        year: document.querySelector("#year").value,
        genre: document.querySelector("#genre").value,
        tags: [document.querySelector("#tags").value]
    };
    searchAjax(data);
}

function handleArtistSearch() {
    let data = {
        qtype: "artist",
        referrer: "artist",
        name: document.querySelector("#artist").value,
        country: document.querySelector("#country").value,
        begin_comparison: document.querySelector("#begin_filter").value,
        begin_date: document.querySelector("#begin_date").value,
        end_comparison: document.querySelector("#end_filter").value,
        end_date: document.querySelector("#end_date").value,
        type: document.querySelector("#type").value
    };
    searchAjax(data);
}

function handleLabelSearch() {
    let data = {
        qtype: "label",
        referrer: "label",
        name: document.querySelector("#label").value,
        country: document.querySelector("#country").value,
        begin_comparison: document.querySelector("#begin_filter").value,
        begin_date: document.querySelector("#begin_date").value,
        end_comparison: document.querySelector("#end_filter").value,
        end_date: document.querySelector("#end_date").value,
        type: document.querySelector("#type").value,
    }
    searchAjax(data);
}

function searchAjax(data) {
    // AJAX function to update #search-results element
    fetch('/dynamic_search', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    })
    .then(function(response) {
        return response.text();
    })
    .then(function(html) {
        document.querySelector("#search-results").innerHTML = html;
    });
}


document.addEventListener('DOMContentLoaded', () => {
    document.addEventListener('click', function(event) {
        // Handle search button click
        if (event.target && event.target.classList.contains('search-btn')) {
            handleSearchButton();
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
            console.log('click');
            handleLabelSearch();
        }
        // Handle /releases, /labels, /artists pagination button clicks
        if (event.target && event.target.classList.contains('dynamic-page-btn')) {
            let direction = event.target.dataset.direction;
            handleDynamicPageButton(direction);
        }
    });
});



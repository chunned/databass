document.addEventListener('DOMContentLoaded', function() {
    let deleteButton = document.querySelector("#delete");
    try {
        deleteButton.addEventListener("click", function() {
            showPopup(deleteButton);
        });
    } catch (error) {
        console.error(error);
    }
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


// Used in search.html to show popup before release is inserted
(function() {
    // Function to create and show the pop-up element
    function showPopup(data) {
        try {
            console.log(data)
            // Perform string substitutions in steps so as to not accidentally alter release information
            const data2 = data.replace(/{'/g, '{"');
            const data3 = data2.replace(/'}/g, '"}');
            const data4 = data3.replace(/':/g, '":');
            const data5 = data4.replace(/ '/g, ' "');
            const data6 = data5.replace(/',/g, '",');
            const data7 = data6.replace(/(12|10|7)" Vinyl/g, '$1\\" Vinyl');

            let jsonStr = data7;

            try {
                const parsed_data = JSON.parse(jsonStr) // Create the pop-up container
                const popup = document.createElement('div');
                popup.className = 'popup';
                popup.innerHTML = `
                    <div class="popup-content">
                        <span class="close-btn">&times;</span>
                        <form action="/submit" method="POST" id="popup-form">
                            <input type="hidden" name="release" value="${parsed_data.release.name}">
                            <input type="hidden" name="artist" value="${parsed_data.artist.name}">
                            <input type="hidden" name="label" value="${parsed_data.label.name}">
                            <input type="hidden" name="release_id" value="${parsed_data.release.mbid}">
                            <input type="hidden" name="artist_id" value="${parsed_data.artist.mbid}">
                            <input type="hidden" name="label_id" value="${parsed_data.label.mbid}">
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
                                        <input type="number" min="0" required id="year" name="release_year" class="search-btn">
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
                // Append the pop-up to the body
                document.body.appendChild(popup);

                // Close the pop-up when the close button is clicked
                popup.querySelector('.close-btn').addEventListener('click', function() {
                    document.body.removeChild(popup);
                });;
            } catch (error) {
                console.error(error);
                console.log(jsonStr);
            }

        } catch (error) {
            console.error('Failed to parse data-item:', error);
            console.log(data-item)
        }
    }



    const searchBtn = document.querySelector("#search");
    searchBtn.addEventListener("click", (event) => {
        data = {
            release: document.querySelector("#release").value,
            artist: document.querySelector("#artist").value
        };
        fetch('/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(function(response) {
            return response.text();
        })
        .then(function(html) {
            document.querySelector("#search-results").innerHTML = html;
            // Attach click event listeners to table rows
            let tableRows = document.querySelectorAll("table tbody tr");
            tableRows.forEach((tableRow) => {
                tableRow.addEventListener("click", function() {
                    const data = tableRow.dataset.item; // Assuming data-item contains JSON
                    showPopup(data);
                });
            });
        });
    })
})();
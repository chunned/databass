import pytest
from databass import create_app

# TODO: this fixture is a duplicate of the same fixture in test_routes.py; figure out how to generalize/reuse a single fixture instead of duplicating the code
@pytest.fixture()
def client():
    app = create_app()
    app.config.update({"TESTING": True})
    with app.test_client() as client:
        yield client

class Artists:
    # Tests for /artists
    def test_artists_successful_page_load(self, client):
        response = client.get("/artists")
        assert response.status_code == 200
        assert b"search-bar" in response.data

class TestArtist:
    # Tests for /artist
    def test_artist_successful_page_load(self, client, mocker):
        pass

    def test_artist_not_found(self, client, mocker):
        mock_artist_data = mocker.patch("databass.db.models.Artist.exists_by_id", return_value=False)
        response = client.get("/artist/99999999999999999999")
        assert response.status_code == 302
        assert b"You should be redirected automatically" in response.data

class TestEdit:
    # Tests for /artist/<id>/edit
    def test_edit_successful_get(self, client):
        """
        Test for successful handling of a GET request, which displays the editable fields
        """

    def test_edit_non_existing_release(self, client):
        """
        Test for successful handling of a GET request for a release that does not exist
        """

    def test_edit_successful_post(self, client):
        """
        Test for successful handling of a POST request, which submits edited data
        """

    def test_edit_failed_post(self, client):
        """
        Test for successful handling of a malformed POST request
        """

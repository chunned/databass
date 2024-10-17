import pytest
from databass import create_app

# TODO: this fixture is a duplicate of the same fixture in test_routes.py; figure out how to generalize/reuse a single fixture instead of duplicating the code
@pytest.fixture()
def client():
    app = create_app()
    app.config.update({"TESTING": True})
    with app.test_client() as client:
        yield client

class TestReleases:
    # Tests for /releases
    def test_releases_successful_page_load(self, client):
        response = client.get("/releases")
        assert response.status_code == 200
        assert b"search-bar" in response.data

class TestRelease:
    # Tests for /release
    def test_release_successful_page_load(self, client, mocker):
        import datetime

        mock_release_data = mocker.MagicMock()
        mock_release_data.id = 1
        mock_release_data.artist_id = 1
        mock_release_data.label_id = 1
        mock_release_data.name = "BLUE LIPS"
        mock_release_data.country = "[Worldwide]"
        mock_release_data.genre = "hiphop"
        mock_release_data.image = "./static/img/release/1.jpg"
        mock_release_data.listen_date = datetime.datetime(2024, 3, 3, 0, 0)
        mock_release_data.mbid = "46004fde-3059-42a8-b399-daa0a18816e0"
        mock_release_data.rating = 70
        mock_release_data.release_year = 2024
        mock_release_data.review = None
        mock_release_data.runtime = 3361000
        mock_release_data.tags = None
        mock_release_data.track_count = 18

        mock_artist_data = mocker.patch(
            "databass.db.models.Artist.exists_by_id",
            return_value={
                "begin_date": datetime.date(1986, 10, 26),
                "country": None,
                "end_date": datetime.date(9999, 12, 31),
                "id": 1,
                "image": "./static/img/artist/1.jpg",
                "mbid": "bce6d667-cde8-485e-b078-c0a05adea36d",
                "name": "ScHoolboy Q",
                "type": "person"
            })

        mock_label_data = mocker.patch(
            "databass.db.models.Label.exists_by_id",
            return_value={
                "begin_date": datetime.date(2004, 1, 1),
                "country": "US",
                "end_date": datetime.date(9999, 12, 31),
                "id": 1,
                "image": None,
                "mbid": '56d2501f-12b7-4cfd-b8f8-e95189ea27f5',
                "name": "Top Dawg Entertainment",
                "type": "Original Production"
            })
        mock_reviews = mocker.patch("databass.db.models.Release.get_reviews",
                                    return_value=[])
        response = client.get("/release/1")
        assert response.status_code == 200
        assert b"release-table" in response.data
        assert b"listened: 2024-03-04" in response.data

    def test_release_not_found(self, client, mocker):
        mock_release_data = mocker.patch("databass.db.models.Release.exists_by_id", return_value=False)
        response = client.get("/release/99999999999999999999")
        assert response.status_code == 302
        assert b"You should be redirected automatically" in response.data

class TestEdit:
    # Tests for /release/<id>/edit
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

class TestDelete:
    # Tests for /delete
    def test_delete_successful(self, client):
        """
        Test for proper handling of a successful deletion
        """

    def test_delete_failure(self, client):
        """
        Test for proper handling of a failed deletion
        """

class TestAddReview:
    # Tests for /release/<id>/add_review
    def test_add_review_success(self, client):
        """
        Test for successful release addition
        """

    def test_add_review_failure(self, client):
        """
        Test for successful handling of a failed release addition
        """

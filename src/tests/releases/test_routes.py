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
    

class TestRelease:
    # Tests for /release


class TestEdit:
    # Tests for /release/<id>/edit

class TestDelete:
    # Tests for /release/<id>/delete

class TestAddReview:
    # Tests for /release/<id>/add_review

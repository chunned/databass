import pytest
from databass import create_app, routes
from datetime import datetime

@pytest.fixture()
def client():
    app = create_app()
    app.config.update({"TESTING": True})
    with app.test_client() as client:
        yield client

class TestGoals:
    # Tests for /goals route
    def test_goals_page_load_success(self, client):
        """
        Test for successful page load triggered by GET request
        """
        response = client.get("/goals")
        assert response.status_code == 200
        assert b"New Goal" in response.data

    def test_goals_page_load_fail(self, client):
        """
        Test for successful handling of unsupported method
        """
        response = client.post("/goals")
        assert response.status_code == 405

    def test_goals_no_goals_found(self, client, mocker):
        """
        Test for correct handling when no goals are found in database
        """
        with mocker.patch("databass.db.models.Goal.get_incomplete", return_value=[]):
            response = client.get("/goals")
            assert response.status_code == 200
            assert b"No existing goals" in response.data

    def test_goals_all_goals_displayed(self, client, mocker):
        """
        Test that all goals available in database are displayed
        """
        mock_goals = [
            {
                "id": 1,
                "start_date": datetime(2024, 1, 1),
                "end_goal": datetime(2025, 1, 1),
                "end_actual": None,
                "type": 'release',
                "amount": 50
            },
            {
                "id": 2,
                "start_date": datetime(2024, 1, 1),
                "end_goal": datetime(2026, 1, 1),
                "end_actual": None,
                "type": 'album',
                "amount": 10
            },
            {
                "id": 3,
                "start_date": datetime(2024, 1, 1),
                "end_goal": datetime(2027, 1, 1),
                "end_actual": None,
                "type": 'label',
                "amount": 250
            }
        ]
        with mocker.patch("databass.db.models.Goal.get_incomplete", return_value=mock_goals):
            response = client.get("/goals")
            assert response.status_code == 200
            assert b"2027-01-01" in response.data
            assert b"10" in response.data
            assert b"release" in response.data

class TestAddGoal:
    # Tests for /add_goal
    # TODO: look into how to set up a database fixture
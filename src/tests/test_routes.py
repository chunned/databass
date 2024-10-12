import pytest
from databass import create_app, routes
from datetime import datetime
from databass.db.models import Goal

@pytest.fixture()
def client():
    app = create_app()
    app.config.update({"TESTING": True})
    with app.test_client() as client:
        yield client

class TestHome:
    # Tests for /, /home
    def test_home_page_load_success(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert b"home_albums_container" in response.data

    def test_home_method_not_allowed(self, client):
        """
        Test for successful handling of unsupported method
        """
        response = client.post("/")
        assert response.status_code == 405
        assert b"Error 405: Method not allowed" in response.data


class TestGoals:
    # Tests for /goals route
    def test_goals_page_load_success(self, client):
        """
        Test for successful page load triggered by GET request
        """
        response = client.get("/goals")
        assert response.status_code == 200
        assert b"New Goal" in response.data
        assert response.location == '/goals'

    def test_goals_page_load_fail(self, client):
        """
        Test for successful handling of unsupported method
        """
        response = client.post("/goals")
        assert response.status_code == 405
        assert b"Error 405: Method not allowed" in response.data

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
    def test_add_goals_method_not_allowed(self, client):
        """
        Test for successful redirection to /goals
        """
        response = client.get("/add_goal")
        assert response.status_code == 405
        assert b"Error 405: Method not allowed" in response.data

    def test_add_goals_no_payload(self, client):
        """
        Test for successful handling of empty payload
        """
        response = client.post("/add_goal")
        assert response.status_code == 200
        assert b"Application Error" in response.data
        assert b"/add_goal received an empty payload" in response.data

    def test_add_goals_goal_construction_error(self, client, mocker):
        """
        Test for successful handling of Goal object construction errors
        """
        data = {'amount': '4', 'end_goal': '2024-10-24', 'start_date': '2024-10-11', 'type': 'release'}
        with mocker.patch("databass.db.construct_item", return_value=None):
            response = client.post("/add_goal", data=data)
            assert b"Application Error" in response.data
            assert b"Construction of Goal object failed" in response.data

    @pytest.mark.parametrize(
        "amount,end_goal,start_date,goal_type",
        [
            ('4', '2024-10-24', '2024-10-11', 'release'),
            ('100000', '2025-01-01', '2030-12-12', 'album'),
            ('4234', '2111-11-11', '3000-01-01', 'label')
         ]
    )
    def test_add_goals_goal_construction_success(self, client, mocker, amount, end_goal, start_date, goal_type):
        """
        Test for successful Goal object construction and insertion
        """
        mock_insert = mocker.patch("databass.db.insert", return_value=2)
        mock_goal = mocker.patch('databass.db.construct_item', autospec=True)
        mock_instance = mock_goal.return_value
        mock_instance.id = 2

        data = {'amount': amount, 'end_goal': end_goal, 'start_date': start_date, 'type': goal_type}
        response = client.post("/add_goal", data=data)

        mock_goal.assert_called_once_with(
            model_name="goal",
            data_dict={
                'amount': amount,
                'end_goal': end_goal,
                'start_date': start_date,
                'type': goal_type
            }
        )
        assert response.status_code == 302
        assert response.location == '/goals'
        mock_insert.assert_called_once_with(mock_goal.return_value)

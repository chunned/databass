import pytest
import requests.exceptions
from databass.api.discogs import Discogs
from requests import Response
import time

class TestUpdateRateLimit:
    # Tests for Discogs.update_rate_limit
    def test_update_rate_limit(self, mocker):
        assert Discogs.is_throttled() is False
        assert Discogs.remaining_requests is None
        mock_response = mocker.Mock(spec=Response)
        mock_response.headers = {"x-discogs-ratelimit-remaining": "20"}
        mock_response.status_code = 200
        mock_request = mocker.patch("databass.api.discogs.requests.get", return_value=mock_response)
        Discogs.request('/database/search?q=Godspeed+You+Black+Emperor&type=artist')
        assert Discogs.remaining_requests == 20
        mock_request.assert_called_once()

class TestIsThrottled:
    # Tests for Discogs.is_throttled
    def test_is_throttled_true(self):
        Discogs.remaining_requests = 1
        assert Discogs.is_throttled() == True

    @pytest.mark.parametrize(
        "remaining_requests",
        [None, 2, 1.1]
    )
    def test_is_throttled_false(self, remaining_requests):
        Discogs.remaining_requests = remaining_requests
        assert Discogs.is_throttled() == False

class TestRequest:
    # Tests for Discogs.request()
    def test_request_success_with_throttle(self, mocker):
        """
        Basic test for a successful request, also:
        Ensure time.sleep(5) gets called if we are throttled
        """
        sleep_spy = mocker.spy(time, 'sleep')
        mock_response = mocker.Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.headers = {"x-discogs-ratelimit-remaining": "0"}
        mock_response.json.return_value = {"mock": "json"}
        mock_req = mocker.patch(
            "databass.api.discogs.requests.get",
            return_value=mock_response
        )
        Discogs.request("mock_endpoint")
        sleep_spy.assert_called_once_with(5)
        mock_req.assert_called_once()

    def test_request_fail_non_200_statcode(self, mocker):
        mock_response = mocker.Mock(spec=Response)
        mock_response.headers = {"x-discogs-ratelimit-remaining": "50"}
        mock_response.status_code = 404
        mock_req = mocker.patch(
            "databass.api.discogs.requests.get",
            return_value=mock_response
        )
        with pytest.raises(requests.exceptions.RequestException, match="Status code"):
            Discogs.request('mock_endpoint')

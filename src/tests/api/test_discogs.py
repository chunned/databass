import pytest
from databass.api.discogs import Discogs
from requests import Response

class TestUpdateRateLimit:
    def test_update_rate_limit(self, mocker):
        assert Discogs.is_throttled() is False
        assert Discogs.remaining_requests is None
        mock_response = mocker.Mock(spec=Response)
        mock_response.headers = {"x-discogs-ratelimit-remaining": "20"}
        mock_response.status_code = 200
        mock_request = mocker.patch("databass.api.discogs.requests.get", return_value=mock_response)
        Discogs.request('/database/search?q=Godspeed+You+Black+Emperor&type=artist')
        assert Discogs.remaining_requests == 20
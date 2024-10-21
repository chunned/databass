import pytest
from databass.api.util import Util

class TestToDate:
    # Tests for Util.to_date()
    import datetime

    @pytest.mark.parametrize(
        "begin_or_end,date_str,expected",
        [
            ("begin", "2024", datetime.datetime.strptime("2024", "%Y").date()),
            ("end", "2024-10", datetime.datetime.strptime("2024-10", "%Y-%m").date()),
            ("begin", "2024-10-21", datetime.datetime.strptime("2024-10-21", "%Y-%m-%d").date()),
            ("end", None, datetime.datetime(year=9999, month=12, day=31).date()),
            ("begin", None, datetime.datetime(year=1, month=1, day=1).date())
        ]
    )
    def test_to_date_success(self, begin_or_end, date_str, expected):
        """Test to verify return of the proper datetime.date object"""
        result = Util.to_date(begin_or_end, date_str)
        assert result == expected

    def test_to_date_fail_no_arguments(self):
        """Test to verify that ValueError is raised when neither argument is given a value"""
        with pytest.raises(ValueError, match="Must be used with either"):
            Util.to_date(None, None)

    def test_to_date_fail_unrecognized_datestr_format(self):
        """Test to verify that ValueError is raised if date_str is an unexpected length"""
        with pytest.raises(ValueError, match="Unexpected date string format"):
            Util.to_date(begin_or_end=None, date_str="2024-1021")

class TestGetPageRange:
    # Tests for Util.get_page_range()
    @pytest.mark.parametrize(
        "per_page,current_page,expected_start,expected_end",
        [(5, 2, 5, 10), (0, 0, 0, 0)]
    )
    def test_get_page_range_success(self, per_page, current_page, expected_start, expected_end):
        result_start, result_end = Util.get_page_range(per_page, current_page)
        assert result_start == expected_start
        assert result_end == expected_end

    @pytest.mark.parametrize(
        "per_page,current_page",
        [(5, None), (None, 0)]
    )
    def test_get_page_range_fail_invalid_input(self, per_page, current_page):
        with pytest.raises(TypeError):
            result_start, result_end = Util.get_page_range(per_page, current_page)

class TestGetImageTypeFromUrl:
    # Tests for Util.get_image_type_from_url()
    @pytest.mark.parametrize(
        "url,expected",
        [
            ("https://something.com/image.jpg", ".jpg"),
            ("https://something.com/image.jpeg", ".jpeg"),
            ("https://something.com/image.png", ".png")
        ]
    )
    def test_get_image_type_from_url_success(self, url, expected):
        result = Util.get_image_type_from_url(url)
        assert result == expected

    def test_get_image_type_from_url_fail_invalid_url(self):
        with pytest.raises(ValueError, match="ERROR: Invalid image type"):
            Util.get_image_type_from_url("https://something.com/image.gif")

class TestGetImageTypeFromBytes:
    # Test Util.get_image_type_from_bytes()
    @pytest.mark.parametrize(
        "bytestr,expected",
        [
            (b"\xff\xd8\xffasdf", ".jpg"),
            (b"\x89PNG\r\n\x1a\n", ".png"),
        ]
    )
    def test_get_image_type_from_bytes_success(self, bytestr, expected):
        result = Util.get_image_type_from_bytes(bytestr)
        assert result == expected

    def test_get_image_type_from_bytes_fail_invalid_bytestr(self):
        with pytest.raises(
                ValueError,
                match="Either image file is invalid or is not a supported filetype - supported types are jpg and png."
        ):
            Util.get_image_type_from_bytes(b"GIF87a")

# class TestGetImage:
    # Tests for Util.get_image()

class TestImgExists:
    # Tests for Util.img_exists()
    @pytest.mark.parametrize(
        "mock_glob_return,expected",
        [
            (['databass/static/img/release/1.png'], '/static/img/release/1.png'),
            ([], False)
        ]
    )
    def test_img_exists_success(self, mock_glob_return, expected, mocker):
        mock_glob = mocker.patch("glob.glob", return_value=mock_glob_return)
        result = Util.img_exists(item_id=1, item_type='release')
        mock_glob.assert_called_once()
        assert result == expected

    @pytest.mark.parametrize(
        "item_id,item_type,expected_exception,expected_message",
        [
            ("1", "release", TypeError, "item_id must be an integer"),
            (1, 1, TypeError, "item_type must be a string"),
            (1, "test", ValueError, "Invalid item_type")
        ]
    )
    def test_img_exists_fail_invalid_input(self, item_id, item_type, expected_exception, expected_message):
        with pytest.raises(expected_exception, match=expected_message):
            Util.img_exists(item_id, item_type)
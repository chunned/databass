from pathlib import Path

import pytest
from databass.api.util import Util

VALID_JPEG_BYTES = bytes([0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46])
VALID_PNG_BYTES = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])
INVALID_BYTES = bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])


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
    """Tests for Util.get_image_type_from_url method."""
    def test_standard_image_urls(self):
        """Test detection of image types from standard URLs with extensions at the end."""
        test_cases = {
            'https://example.com/image.jpg': '.jpg',
            'https://example.com/photo.png': '.png',
            'https://example.com/avatar.webp': '.webp',
            'https://example.com/animation.gif': '.gif'
        }
        for url, expected in test_cases.items():
            assert Util.get_image_type_from_url(url) == expected

    def test_uppercase_extensions(self):
        """Test that uppercase extensions are correctly identified."""
        test_cases = {
            'https://example.com/image.JPG': '.jpg',
            'https://example.com/photo.PNG': '.png',
            'https://example.com/avatar.WEBP': '.webp'
        }
        for url, expected in test_cases.items():
            assert Util.get_image_type_from_url(url) == expected

    def test_extension_in_path(self):
        """Test URLs where the extension appears in the middle of the path."""
        test_cases = {
            'https://example.com/photos/image.jpg/download': '.jpg',
            'https://example.com/image.png/thumbnail': '.png',
            'https://example.com/avatar.webp/small': '.webp'
        }
        for url, expected in test_cases.items():
            assert Util.get_image_type_from_url(url) == expected

    def test_multiple_extensions(self):
        """Test URLs containing multiple extensions - should return the first valid one."""
        url = 'https://example.com/image.jpg.png'
        assert Util.get_image_type_from_url(url) == '.jpg'

    def test_invalid_url(self):
        """Test that invalid URLs raise ValueError."""
        invalid_urls = [
            'https://example.com/image',
            'https://example.com/photo.invalid',
            'https://example.com/picture.doc'
        ]
        for url in invalid_urls:
            with pytest.raises(ValueError):
                Util.get_image_type_from_url(url)

    def test_all_supported_formats(self):
        """Test all supported image formats."""
        formats = ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.tiff', '.tif', '.avif']
        for fmt in formats:
            url = f'https://example.com/image{fmt}'
            assert Util.get_image_type_from_url(url) == fmt

class TestGetImageTypeFromBytes:
    # Test Util.get_image_type_from_bytes()
    def test_from_bytes_jpeg(self):
        """Test to verify JPEG bytes are correctly identified"""
        assert Util.from_bytes(VALID_JPEG_BYTES) == '.jpg'

    def test_from_bytes_png(self):
        """Test to verify PNG bytes are correctly identified"""
        assert Util.from_bytes(VALID_PNG_BYTES) == '.png'

    def test_from_bytes_invalid(self):
        """Test to verify ValueError is raised for invalid image bytes"""
        with pytest.raises(ValueError) as exc_info:
            Util.from_bytes(INVALID_BYTES)
        assert "Unsupported file type" in str(exc_info.value)

    def test_from_bytes_empty(self):
        """Test to verify ValueError is raised for empty bytes"""
        with pytest.raises(ValueError) as exc_info:
            Util.from_bytes(bytes())
        assert "must be at least 8 bytes" in str(exc_info.value)

    def test_from_bytes_partial_header(self):
        """Test to verify ValueError is raised for incomplete image headers"""
        partial_jpeg = VALID_JPEG_BYTES[:3]
        with pytest.raises(ValueError) as exc_info:
            Util.get_image_type_from_bytes(partial_jpeg)
        assert "must be at least 8 bytes" in str(exc_info.value)

# class TestGetImage:
    # Tests for Util.get_image()

class TestImgExists:
    """Test suite for the img_exists utility function"""
    @pytest.mark.parametrize("item_id,item_type,expected,extension", [
        (123, "release", "/static/img/release/123.jpg", "jpg"),
        (456, "artist", "/static/img/artist/456.png", "png"),
        (789, "label", "/static/img/label/789.jpg", "jpg"),
    ])
    def test_existing_image(self, item_id, item_type, expected, extension, monkeypatch):
        """
        Test that the function returns the correct path when an image exists
        """

        def mock_glob(*args, **kwargs):
            return [Path(f"static/img/{item_type}/{item_id}.{extension}")]

        monkeypatch.setattr(Path, "glob", mock_glob)
        result = Util.img_exists(item_id, item_type)
        assert result == expected

    def test_nonexistent_image(self, monkeypatch):
        """
        Test that the function returns None when no image exists
        """

        def mock_glob(*args, **kwargs):
            return []

        monkeypatch.setattr(Path, "glob", mock_glob)
        result = Util.img_exists(123, "release")
        assert result is None

    @pytest.mark.parametrize("item_type", ["RELEASE", "ARTIST", "LABEL"])
    def test_case_insensitive_type(self, item_type, monkeypatch):
        """
        Test that the function handles case-insensitive item types correctly
        """

        def mock_glob(*args, **kwargs):
            return [Path(f"static/img/{item_type.lower()}/123.jpg")]

        monkeypatch.setattr(Path, "glob", mock_glob)
        result = Util.img_exists(123, item_type)
        assert result is not None

    @pytest.mark.parametrize("invalid_type", [
        "album", "band", "invalid", "", "releases", "artists"
    ])
    def test_invalid_item_type(self, invalid_type):
        """
        Test that the function raises ValueError for invalid item types
        """
        with pytest.raises(ValueError) as exc:
            Util.img_exists(123, invalid_type)
        assert "Invalid item_type" in str(exc.value)

    @pytest.mark.parametrize("invalid_id", [
        "123", 1.23, -1, -100, None, [], {}
    ])
    def test_invalid_item_id(self, invalid_id):
        """
        Test that the function raises appropriate errors for invalid item IDs
        """
        if isinstance(invalid_id, int) and invalid_id < 0:
            with pytest.raises(ValueError) as exc:
                Util.img_exists(invalid_id, "release")
            assert "must be a positive integer" in str(exc.value)
        else:
            with pytest.raises(TypeError) as exc:
                Util.img_exists(invalid_id, "release")
            assert "must be a positive integer" in str(exc.value)

import pytest
from databass.pagination import Pager

class TestGetPageRange:
    """Tests for Util.get_page_range() function"""
    @pytest.mark.parametrize("per_page, current_page, expected_start, expected_end", [
        (10, 1, 0, 10),      # First page
        (10, 2, 10, 20),     # Second page
        (5, 3, 10, 15),      # Third page with different page size
        (100, 1, 0, 100),    # Large page size
        (1, 1, 0, 1),        # Minimum valid page size
        (3, 5, 12, 15),      # Later page with small page size
    ])
    def test_get_page_range_valid_inputs(self, per_page, current_page, expected_start, expected_end):
        """Test get_page_range with various valid input combinations"""
        start, end = Pager.get_page_range(per_page, current_page)
        assert start == expected_start
        assert end == expected_end

    @pytest.mark.parametrize("per_page, current_page, error_message", [
        (0, 1, "per_page and current_page must be positive integers"),
        (-5, 1, "per_page and current_page must be positive integers"),
        (10, 0, "per_page and current_page must be positive integers"),
        (10, -1, "per_page and current_page must be positive integers"),
        (-5, -5, "per_page and current_page must be positive integers"),
    ])
    def test_get_page_range_invalid_inputs(self, per_page, current_page, error_message):
        """Test get_page_range with invalid input values"""
        with pytest.raises(ValueError) as exc_info:
            Pager.get_page_range(per_page, current_page)
        assert str(exc_info.value) == error_message

    def test_get_page_range_large_values(self):
        """Test get_page_range with very large input values"""
        per_page = 1000000
        current_page = 1000
        start, end = Pager.get_page_range(per_page, current_page)
        assert start == 999000000
        assert end == 1000000000

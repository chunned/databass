import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from databass import create_app
from databass.db.models import Base, Release, Artist, Label
from databass.db.base import app_db
from flask import Flask


@pytest.fixture
def app():
    """Create and configure a test Flask application"""
    app = create_app()
    app.config.update({"TESTING": True})
    return app

class TestBaseGetAll:
    """
    Test suite for Base.get_all class method

    Uses Release as a concrete model class since Base is not actually used in the database.
    """

    def test_get_all_returns_list(self, mocker):
        """
        Test that get_all returns a list regardless of whether entries exist
        """
        mock_query = mocker.patch('databass.db.base.app_db.session.query')
        mock_query.return_value.all.return_value = []

        result = Release.get_all()
        assert isinstance(result, list)

    def test_get_all_returns_all_entries(self, mocker):
        """
        Test that get_all returns all entries from the database
        """
        mock_entries = [mocker.Mock(), mocker.Mock(), mocker.Mock()]
        mock_query = mocker.patch('databass.db.base.app_db.session.query')
        mock_query.return_value.all.return_value = mock_entries

        result = Release.get_all()
        assert len(result) == 3
        assert result == mock_entries

    def test_get_all_queries_correct_model(self, mocker):
        """
        Test that get_all queries the correct model class
        """
        mock_query = mocker.patch('databass.db.base.app_db.session.query')
        mock_query.return_value.all.return_value = []

        Release.get_all()
        mock_query.assert_called_once_with(Release)

class TestBaseTotalCount:
    """
    Test suite for Base.total_count class method

    Uses Release as a concrete model class since Base is not actually used in the database.
    """
    def test_total_count_returns_integer(self, mocker):
        """
        Test that total_count returns an integer value
        """
        mock_query = mocker.patch('databass.db.base.app_db.session.query')
        mock_query.return_value.count.return_value = 0

        # Mock the session to ensure it returns the count value
        mock_session = mocker.patch('databass.db.base.app_db.session')
        mock_session.query.return_value.count.return_value = 0

        result = Release.total_count()
        print(result)
        assert isinstance(result, int)

    def test_total_count_queries_correct_model(self, mocker):
        """
        Test that total_count queries the correct model class
        """
        mock_query = mocker.patch('databass.db.base.app_db.session.query')
        mock_query.return_value.count.return_value = 0

        Release.total_count()
        mock_query.assert_called_once_with(Release)

    @pytest.mark.parametrize("count_value", [0, 1, 100])
    def test_total_count_returns_correct_value(self, mocker, count_value):
        """
        Test that total_count returns the correct count from the database
        """
        # Mock both query and session to ensure proper return value
        mock_session = mocker.patch('databass.db.base.app_db.session')
        mock_session.query.return_value.count.return_value = count_value

        result = Release.total_count()
        assert result == count_value

    def test_total_count_with_database(self, mocker):
        """
        Test total_count with database operations through mocking
        """
        mock_query = mocker.patch('databass.db.base.app_db.session.query')
        mock_query.return_value.count.return_value = 0

        initial_count = Release.total_count()
        assert initial_count == 0

        # Simulate adding records by changing mock return value
        mock_query.return_value.count.return_value = 3

        final_count = Release.total_count()
        assert final_count == 3


class TestBaseExistsById:
    """Test suite for Base.exists_by_id class method"""

    def test_exists_by_id_returns_none_for_nonexistent_id(self, mocker):
        """Test that exists_by_id returns None when no matching ID is found"""
        mock_query = mocker.patch('databass.db.base.app_db.session.query')
        mock_query.return_value.filter.return_value.one_or_none.return_value = None

        result = Release.exists_by_id(999)
        assert result is None
        mock_query.assert_called_once_with(Release)

    def test_exists_by_id_returns_object_when_found(self, mocker):
        """Test that exists_by_id returns the object when a matching ID is found"""
        mock_release = mocker.Mock()
        mock_query = mocker.patch('databass.db.base.app_db.session.query')
        mock_query.return_value.filter.return_value.one_or_none.return_value = mock_release

        result = Release.exists_by_id(1)
        assert result == mock_release
        mock_query.assert_called_once_with(Release)

    @pytest.mark.parametrize("test_id", [
        None,
        "string_id",
        3.14,
        [],
        {}
    ])
    def test_exists_by_id_with_invalid_id_types(self, mocker, test_id):
        """Test that exists_by_id handles invalid ID types appropriately"""
        mock_query = mocker.patch('databass.db.base.app_db.session.query')

        result = Release.exists_by_id(test_id)
        # Should still attempt to query even with invalid types
        # as SQLAlchemy will handle type conversion/errors
        mock_query.assert_called_once_with(Release)

    def test_exists_by_id_query_construction(self, mocker):
        """Test that exists_by_id constructs the correct query"""
        mock_query = mocker.patch('databass.db.base.app_db.session.query')
        mock_filter = mocker.Mock()
        mock_query.return_value.filter = mock_filter
        mock_filter.return_value.one_or_none.return_value = None

        Release.exists_by_id(1)

        # Verify the query chain
        mock_query.assert_called_once_with(Release)
        mock_filter.assert_called_once()

    def test_exists_by_id_handles_database_error(self, mocker):
        """Test that exists_by_id handles database errors gracefully"""
        mock_query = mocker.patch('databass.db.base.app_db.session.query')
        mock_query.return_value.filter.return_value.one_or_none.side_effect = Exception("Database error")

        result = Release.exists_by_id(1)
        assert result is None
        mock_query.assert_called_once_with(Release)


class TestBaseGetDistinctColumnValues:
    """Test suite for Base.get_distinct_column_values class method"""

    def test_get_distinct_column_values_returns_list(self, mocker):
        """Test that get_distinct_column_values returns a list"""
        mock_query = mocker.patch('databass.db.base.app_db.session.query')
        mock_query.return_value = []

        result = Release.get_distinct_column_values('genre')
        assert isinstance(result, list)

    @pytest.mark.parametrize("column,values", [
        ('genre', ['Rock', 'Jazz', 'Electronic']),
        ('country', ['US', 'UK', 'DE']),
        ('rating', [1, 2, 3, 4, 5]),
    ])
    def test_get_distinct_column_values_returns_correct_values(self, mocker, column, values):
        """Test that get_distinct_column_values returns the correct distinct values for a given column"""
        mock_query = mocker.patch('databass.db.base.app_db.session.query')
        mock_query.return_value = [(value,) for value in values]

        result = Release.get_distinct_column_values(column)
        assert result == values

    def test_get_distinct_column_values_invalid_column(self):
        """Test that get_distinct_column_values raises AttributeError for invalid column name"""
        with pytest.raises(AttributeError):
            Release.get_distinct_column_values('nonexistent_column')

    def test_get_distinct_column_values_handles_empty_results(self, mocker):
        """Test that get_distinct_column_values handles empty result sets correctly"""
        mock_query = mocker.patch('databass.db.base.app_db.session.query')
        mock_query.return_value = []

        result = Release.get_distinct_column_values('genre')
        assert result == []

    def test_get_distinct_column_values_queries_correct_attribute(self, mocker):
        """Test that get_distinct_column_values constructs the query with the correct column attribute"""
        mock_query = mocker.patch('databass.db.base.app_db.session.query')
        mock_query.return_value = []

        Release.get_distinct_column_values('genre')

        # Verify the distinct() call was made on the correct column
        mock_query.assert_called_once()
        args = mock_query.call_args[0]
        assert 'genre' in str(args[0])

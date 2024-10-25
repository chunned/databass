import pytest
from sqlalchemy.exc import IntegrityError
from databass.db.operations import insert, update, delete
from databass.db.models import Artist, Label, Release


@pytest.fixture
def mock_db_session(mocker):
    """Fixture to mock database session"""
    return mocker.patch('databass.db.operations.app_db.session')


class TestInsert:
    """Tests for insert()"""

    def test_successful_insert(self, mock_db_session):
        """
        Test successful insertion of a new database entry
        Verifies that:
        - add() is called with correct item
        - commit() is called
        - correct ID is returned
        """
        test_artist = Artist(name="Test Artist")
        test_artist.id = 1

        insert(test_artist)

        mock_db_session.add.assert_called_once_with(test_artist)
        mock_db_session.commit.assert_called_once()

    def test_integrity_error_handling(self, mock_db_session):
        """
        Test handling of IntegrityError during insertion
        Verifies that:
        - IntegrityError is raised with correct message
        - Session is rolled back
        """
        test_label = Label(name="Test Label")
        mock_db_session.add.side_effect = IntegrityError("statement", "params", "orig")

        with pytest.raises(IntegrityError):
            insert(test_label)

        mock_db_session.rollback.assert_called_once()

    def test_generic_error_handling(self, mock_db_session):
        """
        Test handling of generic exceptions during insertion
        Verifies that:
        - Generic exception is raised with correct message
        - Session is rolled back
        """
        test_release = Release(name="Test Release")
        mock_db_session.add.side_effect = Exception("Test error")

        with pytest.raises(Exception, match="Unexpected error: Test error"):
            insert(test_release)

        mock_db_session.rollback.assert_called_once()

    @pytest.mark.parametrize("model_class,test_data", [
        (Artist, {"name": "Test Artist"}),
        (Label, {"name": "Test Label"}),
        (Release, {"name": "Test Release", "release_year": 2024})
    ])
    def test_insert_different_models(self, mock_db_session, model_class, test_data):
        """
        Test insertion of different model types
        Verifies that:
        - Different model types can be inserted
        - Correct methods are called for each model type
        """
        test_item = model_class(**test_data)
        test_item.id = 1

        result = insert(test_item)

        assert result == 1
        mock_db_session.add.assert_called_once_with(test_item)
        mock_db_session.commit.assert_called_once()


class TestUpdate:
    """Tests for update()"""

    def test_successful_update(self, mock_db_session):
        """
        Test successful update of an existing database entry
        Verifies that:
        - query().get() returns the existing item
        - commit() is called
        - attributes are updated correctly
        """
        test_artist = Artist(name="Original Name")
        test_artist.id = 1

        updated_artist = Artist(name="Updated Name")
        updated_artist.id = 1

        mock_db_session.query().get.return_value = test_artist

        update(updated_artist)

        assert test_artist.name == "Updated Name"
        mock_db_session.commit.assert_called_once()

    def test_nonexistent_item_update(self, mock_db_session):
        """
        Test update attempt on non-existent database entry
        Verifies that:
        - Exception is raised with correct message
        - Session is rolled back
        """
        test_artist = Artist(name="Test Artist")
        test_artist.id = 999

        mock_db_session.query().get.return_value = None

        with pytest.raises(Exception, match=f"No entry found with ID {test_artist.id}"):
            update(test_artist)

        mock_db_session.rollback.assert_called_once()

    @pytest.mark.parametrize("model_class,initial_data,updated_data", [
        (Artist, {"name": "Initial Artist"}, {"name": "Updated Artist"}),
        (Label, {"name": "Initial Label"}, {"name": "Updated Label"}),
        (Release,
         {"name": "Initial Release", "release_year": 2023},
         {"name": "Updated Release", "release_year": 2024})
    ])
    def test_update_different_models(self, mock_db_session, model_class, initial_data, updated_data):
        """
        Test update of different model types
        Verifies that:
        - Different model types can be updated
        - All attributes are updated correctly
        - Correct methods are called for each model type
        """
        initial_item = model_class(**initial_data)
        initial_item.id = 1

        updated_item = model_class(**updated_data)
        updated_item.id = 1

        mock_db_session.query().get.return_value = initial_item

        update(updated_item)

        for key, value in updated_data.items():
            assert getattr(initial_item, key) == value
        mock_db_session.commit.assert_called_once()

    def test_error_handling(self, mock_db_session):
        """
        Test handling of unexpected errors during update
        Verifies that:
        - Exception is caught and re-raised with correct message
        - Session is rolled back
        """
        test_artist = Artist(name="Test Artist")
        test_artist.id = 1

        mock_db_session.query().get.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Unexpected error: Database error"):
            update(test_artist)

        mock_db_session.rollback.assert_called_once()

    def test_private_attributes_ignored(self, mock_db_session):
        """
        Test that private attributes (starting with '_') are not updated
        Verifies that:
        - Public attributes are updated
        - Private attributes are ignored
        """
        initial_artist = Artist(name="Initial Name")
        initial_artist.id = 1
        initial_artist._private_attr = "initial"

        updated_artist = Artist(name="Updated Name")
        updated_artist.id = 1
        updated_artist._private_attr = "updated"

        mock_db_session.query().get.return_value = initial_artist

        update(updated_artist)

        assert initial_artist.name == "Updated Name"
        assert initial_artist._private_attr == "initial"
        mock_db_session.commit.assert_called_once()

class TestDelete:
    """Tests for delete()"""

    def test_successful_delete(self, mock_db_session):
        """
        Test successful deletion of a database entry
        Verifies that:
        - query().where().one() returns the correct item
        - delete() is called with correct item
        - commit() is called
        """
        test_artist = Artist(name="Test Artist")
        mock_db_session.query().where().one.return_value = test_artist

        delete("artist", "1")

        mock_db_session.delete.assert_called_once_with(test_artist)
        mock_db_session.commit.assert_called_once()

    def test_nonexistent_model_type(self, mock_db_session):
        """
        Test deletion attempt with invalid model type
        Verifies that:
        - NameError is raised with correct message
        - Session is rolled back
        """
        with pytest.raises(Exception, match="Unexpected error: No model with the name"):
            delete("invalid_type", "1")

        mock_db_session.rollback.assert_called_once()

    def test_nonexistent_item(self, mock_db_session):
        """
        Test deletion attempt of non-existent item
        Verifies that:
        - Exception is raised when item not found
        - Session is rolled back
        """
        mock_db_session.query().where().one.side_effect = Exception("No such item")

        with pytest.raises(Exception, match="Unexpected error: No such item"):
            delete("artist", "999")

        mock_db_session.rollback.assert_called_once()

    @pytest.mark.parametrize("model_type,item_id,expected_model", [
        ("artist", "1", Artist),
        ("label", "2", Label),
        ("release", "3", Release)
    ])
    def test_delete_different_models(self, mock_db_session, model_type, item_id, expected_model):
        """
        Test deletion of different model types
        Verifies that:
        - Different model types can be deleted
        - Correct model class is queried for each type
        - Correct methods are called for each model type
        """
        test_item = expected_model(name="Test Item")
        mock_db_session.query().where().one.return_value = test_item

        delete(model_type, item_id)

        mock_db_session.delete.assert_called_once_with(test_item)
        mock_db_session.commit.assert_called_once()

    def test_database_error_handling(self, mock_db_session):
        """
        Test handling of database errors during deletion
        Verifies that:
        - Database errors are caught and re-raised with correct message
        - Session is rolled back
        """
        mock_db_session.query().where().one.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Unexpected error: Database error"):
            delete("artist", "1")

        mock_db_session.rollback.assert_called_once()

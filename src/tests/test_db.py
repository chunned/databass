import pytest
from databass import db, models

# TODO: refactor db.py into a module


class TestConstructItem:
    # Test construct_item
    
    @pytest.mark.parametrize(
        'model_name,data_dict',
        [
            ('release', {}),            
            ('artist', {}),            
            ('label', {})            
        ]
    )
    def test_construct_item_success(self, model_name, data_dict):
        """
        Test for a successfully constructed instance of a database model
        """
        result = db.construct_item(model_name, data_dict)

    def test_construct_item_model_name_invalid(self, model_name, data_dict):
        """
        Test for correct handling of an invalid model_name
        """
        result = db.construct_item(model_name, data_dict)

    def test_construct_item_not_found_in_globals(self, model_name, data_dict):
        """
        Test for correct handling of a valid model_name that is not found in globals()
        """
        result = db.construct_item(model_name, data_dict)


class TestGetModel:
    # Test get_model

    @pytest.fixture(
            'globals()',
            return_value = {
            }
        )

    @pytest.mark.parametrize(
       'model_name',
       [(''), (1), (' '), ([]), ('somemodelthatdoesntexist')]
    )
    def test_get_model_model_name_invalid(self, model_name):
        """
        Test for an invalid model name; either wrong type or does not exist
        """
        result = db.get_model(model_name)
        

    @pytest.mark.parametrize(
       'model_name',
       [('release'), ('label'), ('tag'), ('ARTIST'), ('gEnrE')]
    )
    def test_get_model_success(self, model_name):
        """
        Test for successful instantiazation of the model class
        """
        result = db.get_model(model_name)


class TestInsert:
    # Test insert()


class TestUpdate:
    # Test update()


class TestDelete:
    # Test delete()

class TestExists:
    # Test exists()

class TestNextItem:
    # Test next_item()

class TestGetArtistReleases:
    # Test get_artist_releases()

class TestGetLabelReleases:
    # Test get_label_releases()

class TestGetReleaseReviews:
    # Test get_release_reviews()

class TestGetAll:
    # Test get_all()

class TestGetDistinctCol:
    # Test get_distinct_col()

class TestGetAllIdAndImg:
    # Test get_all_id_and_img()

class TestDynamicSearch:
    # Test dynamic_search()

class TestDynamicReleaseSearch:
    # Test dynamic_release_search()

class TestDynamicArtistSearch:
    # Test dynamic_artist_search()

class TestDynamicLabelSearch:
    # Test dynamic_label_search()

class TestDynamicArtistOrLabelQuery:
    # Test dynamic_artist_or_label_query()

class TestApplyDateFilter:
    # Test apply_date_filter()

class TestSubmitManual:
    # Test submit_manual()

class TestGetIncompleteGoals:
    # Test get_incomplete_goals()

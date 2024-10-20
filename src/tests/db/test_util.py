import pytest 
from databass.db.util import *


class MockModel:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

mock_models = {
    'Release': MockModel,
    'Artist': MockModel,
    'Label': MockModel,
    'Goal': MockModel,
    'Review': MockModel,
    'Tag': MockModel,
}

@pytest.fixture
def mock_model_fixture():
    return lambda model_name: mock_models.get(model_name.capitalize(), None)


class TestGetModel:
    # Tests for get_model()
    def test_get_model_success(self, mocker):
        class MockModel:
            pass
        mock_globals = mocker.patch("databass.db.util.globals", return_value={"Model": MockModel})
        result = get_model("Model")
        assert result == MockModel
        mock_globals.assert_called_once()

    @pytest.mark.parametrize(
        "model",
        [1, [1], {"1": 1}, 1.0]
    )
    def test_get_model_fail_invalid_input(self, model):
        with pytest.raises(ValueError, match="model_name must be a string"):
            get_model(model)

    def test_get_model_fail_model_not_found(self, mocker):
        class MockModel:
            pass
        mock_globals = mocker.patch("databass.db.util.globals", return_value={"Model": MockModel})
        with pytest.raises(NameError, match="No model with the name"):
            get_model("TestModel")

class TestConstructItem:
    # Tests for construct_item()
    @pytest.mark.parametrize(
        "model,data_dict",
        [
            ('release',{"name": "Test Release"}),
            ('artist', {"name": "Test Artist"}),
            ('label', {"name": "Test Label"}),
            ('goal', {"name": "Test Goal"}),
            ('review', {"name": "Test Review"}),
            ('tag', {"name": "Test Tag"})
        ]
    )
    def test_construct_item_success(self, model, data_dict, mocker, mock_model_fixture):
        mocker.patch("databass.db.util.get_model", side_effect=mock_model_fixture)
        item = construct_item(model_name=model, data_dict=data_dict)
        expected_class = mock_model_fixture(model)
        name = "Test " + model.capitalize()
        assert isinstance(item, expected_class)
        assert item.name == name


    def test_construct_item_fail_invalid_model_name(self, mocker, mock_model_fixture):
        """
        Test for successful handling of a model name not found in valid_models
        """
        mock_get_model = mocker.patch("databass.db.util.get_model", side_effect=mock_model_fixture)
        data_dict = {"name": "asdf"}
        bad_name = "asdf"
        with pytest.raises(ValueError, match="Invalid model name"):
            construct_item(model_name=bad_name, data_dict=data_dict)
            mock_get_model.assert_called_once_with(bad_name)

# class TestNextItem:
    # Tests for next_item()




class TestMeanAvgAndCount:
    # Tests for mean_avg_and_count()
    def test_mean_avg_and_count_successful_return(self):
        """
        Test for proper handling of successful calculation of average and total count
        """

    def test_mean_avg_and_count_successful_failure(self):
        """
        Test for proper handling of invalid return data 
        """


class TestBayesianAvg:
    # Tests for bayesian_avg()
    @pytest.mark.parametrize(
        "weight,item_avg,mean_avg",
        [
            (2.0, 1.0, None),
            (2.0, None, 3.0),
            (None, 1.0, 3.0)
        ]
    )
    def test_bayesian_avg_missing_value(self, weight, item_avg, mean_avg):
        """
        Test for correct handling of input with missing values
        """
        with pytest.raises(ValueError, match="Input missing one of the required values"):
            bayesian_avg(
                    item_weight=weight,
                    item_avg=item_avg,
                    mean_avg=mean_avg
            )

    @pytest.mark.parametrize(
        "weight,item_avg,mean_avg,expected",
        [
            (1.0, 2.0, 3.0, 2.0),
            (2.0, 3.0, 1.0, 5.0),
            (3.0, 1.0, 2.0, -1.0)
        ]
    )
    def test_bayesian_avg_correct_return(self, weight, item_avg, mean_avg, expected):
        """
        Test for correct handling of valid input
        """
        result = bayesian_avg(
                item_weight=weight,
                item_avg=item_avg,
                mean_avg=mean_avg
        )
        assert result == expected
        
class TestGetAllStats:
    # Tests for get_all_stats()
    def test_get_all_stats_success(self):
        """
        Test for correct handling of successfully returned stats data
        """

    def test_get_all_stats_fail(self):
        """
        Test for successful handling of errored stats function result
        """



class TestHandleSubmitData:
    # Tests for handle_submit_data()
    def test_handle_submit_test_success(self):
        pass
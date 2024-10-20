import pytest 
from databass.db.util import *


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
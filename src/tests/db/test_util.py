import pytest 
from databass.db.util import *


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
    def test_get_all_stats_successful_error_handling(self):
        """
        Test for successful handling of errored stats function result
        """

    def test_get_all_stats_successful_return(self):
        """
        Test for correct handling of successfully returned stats data
        """



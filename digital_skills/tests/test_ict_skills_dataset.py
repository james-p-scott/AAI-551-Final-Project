"""
test_ict_skills_dataset.py

Pytest tests for ict_skills_dataset.ICTSkillsDataset.
"""

import os
import sys

import pytest
import pandas as pd

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_TESTS_DIR))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from digital_skills.ict_skills_dataset import ICTSkillsDataset


class TestICTSkillsDataset:
    """
    Tests for ict_skills_dataset.ICTSkillsDataset.

    setup_method loads the 'safety' dataset before each test. The safety
    category is used because it is the smallest CSV, keeping individual
    test execution fast.
    """

    def setup_method(self):
        # Load the safety dataset before each test.
        self.ds = ICTSkillsDataset("safety")

    def teardown_method(self):
        # Release the dataset reference after each test.
        self.ds = None

    def test_loads_dataframe(self):
        # df attribute should be a non-empty DataFrame after construction.
        assert self.ds.df is not None
        assert isinstance(self.ds.df, pd.DataFrame)
        assert len(self.ds.df) > 0

    def test_available_countries_populated(self):
        # available_countries should be a non-empty sorted list of strings.
        assert isinstance(self.ds.available_countries, list)
        assert len(self.ds.available_countries) > 0
        assert self.ds.available_countries == sorted(self.ds.available_countries)

    def test_available_years_populated(self):
        # available_years should be a non-empty sorted list of ints.
        assert isinstance(self.ds.available_years, list)
        assert len(self.ds.available_years) > 0
        assert all(isinstance(y, int) for y in self.ds.available_years)
        assert self.ds.available_years == sorted(self.ds.available_years)

    def test_len_matches_dataframe_row_count(self):
        # __len__ should return the same count as len(ds.df).
        assert len(self.ds) == len(self.ds.df)

    def test_str_contains_category_name(self):
        # __str__ should include the skill category name.
        assert "safety" in str(self.ds)

    def test_invalid_category_raises_value_error(self):
        # Constructing with an unrecognised category should raise ValueError.
        with pytest.raises(ValueError):
            ICTSkillsDataset("not-a-real-category")

    def test_get_totals_excludes_breakdown_rows(self):
        # get_totals should return only rows where seriesParent is NaN.
        totals = self.ds.get_totals()
        assert totals["seriesParent"].isna().all()

    def test_get_by_gender_male_contains_only_male_rows(self):
        # get_by_gender('male') rows should all contain 'HHCMale' in seriesCode.
        male_df = self.ds.get_by_gender("male")
        assert not male_df.empty
        assert male_df["seriesCode"].str.contains("HHCMale").all()

    def test_get_by_gender_female_contains_only_female_rows(self):
        # get_by_gender('female') rows should all contain 'HHCFemale' in seriesCode.
        female_df = self.ds.get_by_gender("female")
        assert not female_df.empty
        assert female_df["seriesCode"].str.contains("HHCFemale").all()

    def test_get_by_gender_invalid_raises_value_error(self):
        # get_by_gender with an unsupported value should raise ValueError.
        with pytest.raises(ValueError):
            self.ds.get_by_gender("other")

    def test_get_by_urban_rural_urban(self):
        # get_by_urban_rural('urban') rows should contain 'HHCUrbanUsers'.
        urban_df = self.ds.get_by_urban_rural("urban")
        assert not urban_df.empty
        assert urban_df["seriesCode"].str.contains("HHCUrbanUsers").all()

    def test_get_by_urban_rural_invalid_raises_value_error(self):
        # get_by_urban_rural with an unsupported value should raise ValueError.
        with pytest.raises(ValueError):
            self.ds.get_by_urban_rural("suburban")

    def test_filter_by_year_returns_correct_rows(self):
        # filter_by_year should return only rows for the requested year.
        year = self.ds.available_years[0]
        result = self.ds.filter_by_year(year)
        assert not result.empty
        assert (result["dataYear"] == year).all()

    def test_filter_by_year_invalid_raises_value_error(self):
        # filter_by_year with a year not in the dataset should raise ValueError.
        with pytest.raises(ValueError):
            self.ds.filter_by_year(1800)

    def test_filter_by_country_returns_correct_rows(self):
        # filter_by_country should return only rows for the requested ISO code.
        iso = self.ds.available_countries[0]
        result = self.ds.filter_by_country(iso)
        assert not result.empty
        assert (result["entityIso"] == iso).all()

    def test_filter_by_country_invalid_raises_value_error(self):
        # filter_by_country with an ISO not in the dataset should raise ValueError.
        with pytest.raises(ValueError):
            self.ds.filter_by_country("ZZZ")

    def test_get_summary_stats_keys(self):
        # get_summary_stats should return a dict with all expected keys.
        stats = self.ds.get_summary_stats()
        for key in ("category", "count", "mean", "median", "stdev", "min", "max"):
            assert key in stats

    def test_get_summary_stats_mean_in_valid_range(self):
        # get_summary_stats mean should be a percentage between 0 and 100.
        stats = self.ds.get_summary_stats()
        assert 0.0 <= stats["mean"] <= 100.0

    def test_get_summary_stats_min_lte_max(self):
        # get_summary_stats min should not exceed max.
        stats = self.ds.get_summary_stats()
        assert stats["min"] <= stats["max"]

    def test_get_by_age_group_returns_filtered_rows(self):
        # get_by_age_group should return rows whose seriesCode contains the band pattern.
        result = self.ds.get_by_age_group("15to24")
        assert isinstance(result, pd.DataFrame)
        if not result.empty:
            assert result["seriesCode"].str.contains("HHC15to24").all()

    def test_get_by_age_group_empty_string_raises_value_error(self):
        # get_by_age_group with an empty string should raise ValueError.
        with pytest.raises(ValueError):
            self.ds.get_by_age_group("")

if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])

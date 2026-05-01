"""
test_digital_skills_analysis.py

Pytest tests for digital_skills_analysis module-level functions.
"""

import os
import sys

import pytest
import pandas as pd

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_TESTS_DIR))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from digital_skills.ict_skills_dataset import ICTSkillsDataset, SKILL_CATEGORY_FILES
from digital_skills.digital_skills_analysis import (
    load_all_ict_skill_datasets,
    load_skill_level_summary,
    iter_country_data,
    run_digital_literacy_analysis,
)


class TestDigitalSkillsAnalysis:
    """
    Tests for digital_skills_analysis module-level functions.

    setup_method loads the safety dataset (smallest CSV) for tests that
    need a single DataFrame. Tests requiring all five datasets load them
    inline to keep setup cost proportional to what is actually needed.
    """

    def setup_method(self):
        """Load the safety dataset before each test."""
        self.ds = ICTSkillsDataset("safety")

    def teardown_method(self):
        """Release the dataset reference after each test."""
        self.ds = None

    def test_load_all_ict_skill_datasets_returns_five(self):
        """load_all_ict_skill_datasets should return exactly five ICTSkillsDataset objects."""
        datasets = load_all_ict_skill_datasets()
        assert len(datasets) == len(SKILL_CATEGORY_FILES)

    def test_load_all_ict_skill_datasets_correct_types(self):
        """Every item returned by load_all_ict_skill_datasets should be an ICTSkillsDataset."""
        datasets = load_all_ict_skill_datasets()
        assert all(isinstance(ds, ICTSkillsDataset) for ds in datasets)

    def test_load_all_ict_skill_datasets_covers_all_categories(self):
        """The loaded datasets should cover every key in SKILL_CATEGORY_FILES."""
        datasets = load_all_ict_skill_datasets()
        loaded_categories = {ds.skill_category for ds in datasets}
        assert loaded_categories == set(SKILL_CATEGORY_FILES.keys())

    def test_load_skill_level_summary_returns_dataframe(self):
        """load_skill_level_summary should return a non-empty DataFrame."""
        df = load_skill_level_summary()
        assert df is not None
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_iter_country_data_yields_tuples(self):
        """iter_country_data should yield (str, DataFrame) tuples."""
        totals = self.ds.get_totals()
        first = next(iter_country_data(totals))
        assert isinstance(first, tuple)
        assert len(first) == 2
        assert isinstance(first[0], str)
        assert isinstance(first[1], pd.DataFrame)

    def test_iter_country_data_yields_correct_country_rows(self):
        """Each DataFrame yielded should contain only rows for the matching ISO."""
        totals = self.ds.get_totals()
        for iso, country_df in iter_country_data(totals):
            assert (country_df["entityIso"] == iso).all()
            break  # one iteration is sufficient

    def test_iter_country_data_missing_column_raises_value_error(self):
        """iter_country_data should raise ValueError when entityIso column is absent."""
        bad_df = pd.DataFrame({"otherColumn": [1, 2, 3]})
        with pytest.raises(ValueError):
            next(iter_country_data(bad_df))

    def test_iter_country_data_covers_all_unique_countries(self):
        """iter_country_data should yield one entry per unique ISO in the DataFrame."""
        totals = self.ds.get_totals()
        expected = set(totals["entityIso"].dropna().unique())
        yielded = {iso for iso, _ in iter_country_data(totals)}
        assert yielded == expected

    def test_run_digital_literacy_analysis_returns_expected_keys(self):
        """run_digital_literacy_analysis should return a dict with all expected keys."""
        results = run_digital_literacy_analysis()
        for key in ("analyzer", "datasets", "summary_df", "stats_results", "gap_countries"):
            assert key in results

if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])

"""
test_digital_literacy_predictor.py

Pytest tests for digital_literacy_predictor.DigitalLiteracyPredictor.
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
from digital_skills.digital_skills_analyzer import DigitalSkillsAnalyzer
from digital_skills.digital_literacy_predictor import DigitalLiteracyPredictor


class TestDigitalLiteracyPredictor:
    """
    Tests for digital_literacy_predictor.DigitalLiteracyPredictor.

    setup_method constructs an analyzer from the safety and problem-solving
    datasets (two categories that have multi-year data for KOR), then wraps
    it in a predictor. KOR is used throughout because it has one of the longest
    time-series records in the ITU dataset.
    """

    def setup_method(self):
        """Build analyzer and predictor before each test."""
        self.ds_safety = ICTSkillsDataset("safety")
        self.ds_problem = ICTSkillsDataset("problem-solving")
        self.analyzer = DigitalSkillsAnalyzer([self.ds_safety, self.ds_problem])
        self.predictor = DigitalLiteracyPredictor(self.analyzer)

    def teardown_method(self):
        """Release references after each test."""
        self.ds_safety = None
        self.ds_problem = None
        self.analyzer = None
        self.predictor = None

    # --- construction ---

    def test_invalid_analyzer_type_raises_type_error(self):
        """Passing a non-DigitalSkillsAnalyzer should raise TypeError."""
        with pytest.raises(TypeError):
            DigitalLiteracyPredictor("not-an-analyzer")

    def test_str_contains_trained_model_info(self):
        """__str__ should reflect trained models after fit is called."""
        self.predictor.fit("KOR", "safety")
        summary = str(self.predictor)
        assert "KOR" in summary
        assert "safety" in summary

    # --- fit ---

    def test_fit_returns_expected_keys(self):
        """fit should return a dict with country_iso, skill_category, epochs, final_loss."""
        result = self.predictor.fit("KOR", "safety")
        for key in ("country_iso", "skill_category", "epochs", "final_loss"):
            assert key in result

    def test_fit_stores_model_in_cache(self):
        """fit should cache the trained model under (country_iso, skill_category)."""
        self.predictor.fit("KOR", "safety")
        assert ("KOR", "safety") in self.predictor._models

    def test_fit_unknown_country_raises_value_error(self):
        """fit with a country not in the dataset should raise ValueError."""
        with pytest.raises(ValueError):
            self.predictor.fit("ZZZ", "safety")

    def test_fit_final_loss_is_non_negative(self):
        """fit final_loss should be >= 0."""
        result = self.predictor.fit("KOR", "safety")
        assert result["final_loss"] >= 0.0

    # --- predict ---

    def test_predict_returns_dataframe(self):
        """predict should return a non-empty DataFrame."""
        result = self.predictor.predict("KOR", "safety", [2025, 2026])
        assert isinstance(result, pd.DataFrame)
        assert not result.empty

    def test_predict_has_expected_columns(self):
        """predict result should have year, predicted_value, and skill_category columns."""
        result = self.predictor.predict("KOR", "safety", [2025])
        for col in ("year", "predicted_value", "skill_category"):
            assert col in result.columns

    def test_predict_row_count_matches_years(self):
        """predict should return exactly one row per requested year."""
        years = [2025, 2026, 2027]
        result = self.predictor.predict("KOR", "safety", years)
        assert len(result) == len(years)

    def test_predict_values_clamped_to_valid_range(self):
        """All predicted values should be between 0 and 100."""
        result = self.predictor.predict("KOR", "safety", list(range(2025, 2035)))
        assert (result["predicted_value"] >= 0.0).all()
        assert (result["predicted_value"] <= 100.0).all()

    def test_predict_auto_fits_if_not_trained(self):
        """predict should train the model automatically if fit has not been called."""
        fresh_predictor = DigitalLiteracyPredictor(self.analyzer)
        assert ("KOR", "safety") not in fresh_predictor._models
        result = fresh_predictor.predict("KOR", "safety", [2025])
        assert not result.empty
        assert ("KOR", "safety") in fresh_predictor._models

    def test_predict_empty_years_raises_value_error(self):
        """predict with an empty years list should raise ValueError."""
        with pytest.raises(ValueError):
            self.predictor.predict("KOR", "safety", [])

    # --- predict_all_categories ---

    def test_predict_all_categories_returns_dataframe(self):
        """predict_all_categories should return a non-empty DataFrame."""
        result = self.predictor.predict_all_categories("KOR", years_ahead=3)
        assert isinstance(result, pd.DataFrame)
        assert not result.empty

    def test_predict_all_categories_covers_loaded_categories(self):
        """predict_all_categories should include all loaded skill categories."""
        result = self.predictor.predict_all_categories("KOR", years_ahead=2)
        returned_cats = set(result["skill_category"].unique())
        loaded_cats = {ds.skill_category for ds in self.analyzer.datasets}
        assert loaded_cats.issubset(returned_cats)

    def test_predict_all_categories_correct_year_count(self):
        """predict_all_categories should return exactly years_ahead + 1 rows per category,
        spanning a consecutive range of years_ahead years."""
        years_ahead = 3
        result = self.predictor.predict_all_categories("KOR", years_ahead=years_ahead)
        for cat, group in result.groupby("skill_category"):
            assert len(group) == years_ahead + 1
            assert group["year"].max() - group["year"].min() == years_ahead

    def test_predict_all_categories_zero_years_ahead_raises(self):
        """predict_all_categories with years_ahead=0 should raise ValueError."""
        with pytest.raises(ValueError):
            self.predictor.predict_all_categories("KOR", years_ahead=0)

    def test_predict_all_categories_unknown_country_raises(self):
        """predict_all_categories for a country with no data should raise ValueError."""
        with pytest.raises(ValueError):
            self.predictor.predict_all_categories("ZZZ")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])

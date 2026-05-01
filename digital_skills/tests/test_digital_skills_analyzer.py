"""
test_digital_skills_analyzer.py

Pytest tests for digital_skills_analyzer.DigitalSkillsAnalyzer.
"""

import os
import sys

import pytest
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_TESTS_DIR))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from digital_skills.ict_skills_dataset import ICTSkillsDataset 
from digital_skills.digital_skills_analyzer import DigitalSkillsAnalyzer 


class TestDigitalSkillsAnalyzer:
    """
    Tests for digital_skills_analyzer.DigitalSkillsAnalyzer.

    setup_method constructs an analyzer from a fresh safety dataset before
    each test. A second problem-solving dataset is loaded for tests that
    require multiple categories.
    """

    def setup_method(self):
        """Load datasets and build the analyzer before each test."""
        self.ds_safety = ICTSkillsDataset("safety")
        self.ds_problem = ICTSkillsDataset("problem-solving")
        self.analyzer = DigitalSkillsAnalyzer([self.ds_safety])
        self.year = self.ds_safety.available_years[-1]  # most recent year

    def teardown_method(self):
        """Release all references after each test."""
        self.ds_safety = None
        self.ds_problem = None
        self.analyzer = None

    def test_str_lists_all_datasets(self):
        """__str__ should mention every loaded skill category."""
        summary = str(self.analyzer)
        assert "safety" in summary

    def test_empty_datasets_list_raises_value_error(self):
        """Constructing with an empty list should raise ValueError."""
        with pytest.raises(ValueError):
            DigitalSkillsAnalyzer([])

    def test_non_dataset_item_raises_type_error(self):
        """Constructing with a non-ICTSkillsDataset item should raise TypeError."""
        with pytest.raises(TypeError):
            DigitalSkillsAnalyzer(["not-a-dataset"])

    def test_add_merges_categories(self):
        """__add__ should produce an analyzer with both categories combined."""
        analyzer2 = DigitalSkillsAnalyzer([self.ds_problem])
        merged = self.analyzer + analyzer2
        categories = [ds.skill_category for ds in merged.datasets]
        assert "safety" in categories
        assert "problem-solving" in categories

    def test_add_deduplicates_categories(self):
        """__add__ should not duplicate a category present in both analyzers."""
        analyzer2 = DigitalSkillsAnalyzer([self.ds_safety])
        merged = self.analyzer + analyzer2
        categories = [ds.skill_category for ds in merged.datasets]
        assert categories.count("safety") == 1

    def test_add_wrong_type_raises_type_error(self):
        """__add__ with a non-DigitalSkillsAnalyzer should raise TypeError."""
        with pytest.raises(TypeError):
            _ = self.analyzer + "not-an-analyzer"

    def test_rank_countries_returns_dataframe(self):
        """rank_countries_by_skill should return a non-empty DataFrame."""
        result = self.analyzer.rank_countries_by_skill("safety", self.year, top_n=5)
        assert isinstance(result, pd.DataFrame)
        assert not result.empty

    def test_rank_countries_has_expected_columns(self):
        """rank_countries_by_skill result should contain entityIso and mean_value."""
        result = self.analyzer.rank_countries_by_skill("safety", self.year, top_n=5)
        assert "entityIso" in result.columns
        assert "mean_value" in result.columns

    def test_rank_countries_top_n_limits_results(self):
        """rank_countries_by_skill with top_n=3 should return at most 6 rows."""
        result = self.analyzer.rank_countries_by_skill("safety", self.year, top_n=3)
        assert len(result) <= 6  # top 3 + bottom 3

    def test_rank_countries_invalid_top_n_raises_value_error(self):
        """rank_countries_by_skill with top_n=0 should raise ValueError."""
        with pytest.raises(ValueError):
            self.analyzer.rank_countries_by_skill("safety", self.year, top_n=0)

    def test_identify_skill_gaps_returns_sorted_list(self):
        """identify_skill_gaps should return a sorted list of ISO strings."""
        gaps = self.analyzer.identify_skill_gaps(threshold=50.0)
        assert isinstance(gaps, list)
        assert gaps == sorted(gaps)

    def test_identify_skill_gaps_threshold_100_returns_all_countries(self):
        """With threshold=100 every country should be returned as a gap country."""
        gaps = self.analyzer.identify_skill_gaps(threshold=100.0)
        assert len(gaps) == len(self.ds_safety.available_countries)

    def test_identify_skill_gaps_invalid_threshold_raises_value_error(self):
        """identify_skill_gaps with threshold > 100 should raise ValueError."""
        with pytest.raises(ValueError):
            self.analyzer.identify_skill_gaps(threshold=101.0)

    def test_compare_skill_categories_returns_dict(self):
        """compare_skill_categories should return a dict for a known country."""
        iso = self.ds_safety.available_countries[0]
        result = self.analyzer.compare_skill_categories(iso)
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_compare_skill_categories_no_year_uses_latest(self):
        """compare_skill_categories with no year should use each dataset's latest year."""
        iso = self.ds_safety.available_countries[0]
        # Derive the latest year for this specific country from the dataset
        totals = self.ds_safety.get_totals()
        country_totals = totals[totals["entityIso"] == iso]
        latest_year = int(country_totals["dataYear"].max())
        result_no_year = self.analyzer.compare_skill_categories(iso)
        result_explicit = self.analyzer.compare_skill_categories(iso, year=latest_year)
        assert result_no_year == result_explicit

    def test_compare_skill_categories_unknown_country_raises_value_error(self):
        """compare_skill_categories with an unknown ISO should raise ValueError."""
        with pytest.raises(ValueError):
            self.analyzer.compare_skill_categories("ZZZ")

    def test_analyze_skill_trends_returns_dataframe(self):
        """analyze_skill_trends should return a DataFrame with expected columns."""
        iso = self.ds_safety.available_countries[0]
        result = self.analyzer.analyze_skill_trends(iso)
        assert isinstance(result, pd.DataFrame)
        assert "dataYear" in result.columns
        assert "mean_value" in result.columns

    # --- compare_basic_vs_above_basic ---

    def test_compare_basic_vs_above_basic_global_returns_dataframe(self):
        """No args should return a non-empty DataFrame."""
        result = self.analyzer.compare_basic_vs_above_basic()
        assert isinstance(result, pd.DataFrame)
        assert not result.empty

    def test_compare_basic_vs_above_basic_has_expected_columns(self):
        """Result must contain skill_category, basic, and above_basic columns."""
        result = self.analyzer.compare_basic_vs_above_basic()
        assert "skill_category" in result.columns
        assert "basic" in result.columns
        assert "above_basic" in result.columns

    def test_compare_basic_vs_above_basic_sorted_by_category(self):
        """Rows should be sorted alphabetically by skill_category."""
        result = self.analyzer.compare_basic_vs_above_basic()
        categories = result["skill_category"].tolist()
        assert categories == sorted(categories)

    def test_compare_basic_vs_above_basic_country_filter(self):
        """Filtering by a known country should return a non-empty DataFrame."""
        result = self.analyzer.compare_basic_vs_above_basic(country_iso="CAN")
        assert isinstance(result, pd.DataFrame)
        assert not result.empty

    def test_compare_basic_vs_above_basic_year_filter(self):
        """Filtering by a valid year should return a non-empty DataFrame."""
        result = self.analyzer.compare_basic_vs_above_basic(year=2023)
        assert isinstance(result, pd.DataFrame)
        assert not result.empty

    def test_compare_basic_vs_above_basic_country_and_year(self):
        """Filtering by both country and year should return a non-empty DataFrame."""
        result = self.analyzer.compare_basic_vs_above_basic(country_iso="KOR", year=2023)
        assert isinstance(result, pd.DataFrame)
        assert not result.empty

    def test_compare_basic_vs_above_basic_values_are_rounded(self):
        """basic and above_basic values should be rounded to at most 2 decimal places."""
        result = self.analyzer.compare_basic_vs_above_basic()
        for col in ("basic", "above_basic"):
            for val in result[col].dropna():
                assert round(val, 2) == val

    def test_compare_basic_vs_above_basic_invalid_country_raises(self):
        """Unknown country ISO should raise ValueError."""
        with pytest.raises(ValueError):
            self.analyzer.compare_basic_vs_above_basic(country_iso="ZZZ")

    def test_compare_basic_vs_above_basic_invalid_year_raises(self):
        """A year with no data should raise ValueError."""
        with pytest.raises(ValueError):
            self.analyzer.compare_basic_vs_above_basic(year=1900)

    # --- analyze_gender_gap ---

    def test_analyze_gender_gap_returns_dataframe(self):
        """analyze_gender_gap should return a DataFrame with expected columns."""
        # Derive a country that actually has gender-disaggregated rows
        iso = self.ds_safety.get_by_gender("male")["entityIso"].dropna().iloc[0]
        result = self.analyzer.analyze_gender_gap(iso)
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        for col in ("skill_category", "male_mean", "female_mean", "gap"):
            assert col in result.columns

    def test_analyze_gender_gap_unknown_country_raises(self):
        """analyze_gender_gap with a country that has no gender data should raise ValueError."""
        with pytest.raises(ValueError):
            self.analyzer.analyze_gender_gap("ZZZ")

    # --- analyze_age_group_distribution ---

    def test_analyze_age_group_distribution_returns_dataframe(self):
        """analyze_age_group_distribution should return a DataFrame with expected columns."""
        age_df = self.ds_safety.get_by_age_group("15to24")
        if age_df.empty:
            pytest.skip("No age-disaggregated data in safety dataset.")
        iso = age_df["entityIso"].dropna().iloc[0]
        result = self.analyzer.analyze_age_group_distribution(iso)
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        for col in ("skill_category", "age_band", "mean_value"):
            assert col in result.columns

    def test_analyze_age_group_distribution_unknown_country_raises(self):
        """analyze_age_group_distribution with no matching data should raise ValueError."""
        with pytest.raises(ValueError):
            self.analyzer.analyze_age_group_distribution("ZZZ")

    # --- plot methods ---

    def test_plot_global_skill_distribution_returns_figure(self):
        """plot_global_skill_distribution should return a matplotlib Figure."""
        fig = self.analyzer.plot_global_skill_distribution()
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_plot_skill_category_comparison_returns_figure(self):
        """plot_skill_category_comparison should return a matplotlib Figure."""
        iso = self.ds_safety.available_countries[0]
        fig = self.analyzer.plot_skill_category_comparison([iso])
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_plot_gender_gap_returns_figure(self):
        """plot_gender_gap should return a matplotlib Figure."""
        iso = self.ds_safety.get_by_gender("male")["entityIso"].dropna().iloc[0]
        fig = self.analyzer.plot_gender_gap([iso], skill_category="safety")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])

"""
digital_skills_analyzer.py

Defines the DigitalSkillsAnalyzer class, which composes multiple
ICTSkillsDataset instances to perform cross-category ICT skills analysis
and generate matplotlib visualizations.
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# Ensure the project root is on sys.path (same pattern as ict_skills_dataset.py)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from digital_skills.ict_skills_dataset import ICTSkillsDataset  # noqa: E402


class DigitalSkillsAnalyzer:
    """
    Composes a collection of ICTSkillsDataset instances to enable
    cross-category ICT skills analysis and visualization.

    Demonstrates the composition relationship: a DigitalSkillsAnalyzer has
    one or more ICTSkillsDataset objects and delegates data-access operations
    to them.
    """

    def __init__(self, datasets: list):
        """
        Construct a DigitalSkillsAnalyzer from a list of ICTSkillsDataset instances.
        Parameters:
            datasets (list): One or more loaded ICTSkillsDataset instances to analyze.
        Raises:
            TypeError: If datasets is not a list or contains non-ICTSkillsDataset items.
            ValueError: If datasets is an empty list.
        """
        if not isinstance(datasets, list):
            raise TypeError("datasets must be a list of ICTSkillsDataset instances.")
        if len(datasets) == 0:
            raise ValueError("datasets list must not be empty.")
        for item in datasets:
            if not isinstance(item, ICTSkillsDataset):
                raise TypeError(
                    f"All items in datasets must be ICTSkillsDataset instances, "
                    f"got {type(item).__name__}."
                )

        # Mutable list attribute — holds composition of ICTSkillsDataset objects
        self.datasets: list = list(datasets)

        # Internal cache for the combined DataFrame (built lazily on first use)
        self._combined_df: pd.DataFrame | None = None


    def __str__(self) -> str:
        """
        Return a human-readable summary of the analyzer's loaded datasets.
        Returns:
            str: String listing each managed skill category and its row count.
        """
        lines = [f"DigitalSkillsAnalyzer — {len(self.datasets)} dataset(s):"]
        for ds in self.datasets:
            lines.append(f"  [{ds.skill_category}]  {len(ds):,} rows")
        return "\n".join(lines)

    def __add__(self, other: "DigitalSkillsAnalyzer") -> "DigitalSkillsAnalyzer":
        """
        Merge two DigitalSkillsAnalyzer instances into a new one.
        The resulting dataset list is the union of both analyzers' datasets,
        de-duplicated by skill category.

        Parameters:
            other (DigitalSkillsAnalyzer): Another analyzer to merge with.
        Returns:
            DigitalSkillsAnalyzer: New instance with the union of both dataset lists.
        Raises:
            TypeError: If other is not a DigitalSkillsAnalyzer.
        """
        if not isinstance(other, DigitalSkillsAnalyzer):
            raise TypeError(
                f"Cannot add DigitalSkillsAnalyzer and {type(other).__name__}."
            )
        # De-duplicate by skill_category — keep self's version on collision
        seen = {ds.skill_category for ds in self.datasets}
        merged = list(self.datasets)
        for ds in other.datasets:
            if ds.skill_category not in seen:
                merged.append(ds)
                seen.add(ds.skill_category)
        return DigitalSkillsAnalyzer(merged)


    def _get_combined_totals(self) -> pd.DataFrame:
        """
        Build and cache a combined DataFrame of total-population rows from all
        managed datasets, with a skill_category column added.

        Returns:
            DataFrame: Combined total-population rows tagged with skill_category.
        """
        if self._combined_df is not None:
            return self._combined_df

        frames = []
        for ds in self.datasets:
            totals = ds.get_totals().copy()
            # Tag each row with its skill category for cross-category analysis
            totals["skill_category"] = ds.skill_category
            frames.append(totals)

        self._combined_df = pd.concat(frames, ignore_index=True)
        return self._combined_df

    def _get_dataset(self, skill_category: str) -> ICTSkillsDataset:
        """
        Retrieve a managed ICTSkillsDataset by skill category name.

        Parameters:
            skill_category (str): Category name to look up.
        Returns:
            ICTSkillsDataset: The matching dataset instance.
        Raises:
            ValueError: If the category is not managed by this analyzer.
        """
        for ds in self.datasets:
            if ds.skill_category == skill_category:
                return ds
        available = [ds.skill_category for ds in self.datasets]
        raise ValueError(
            f"Skill category '{skill_category}' is not loaded in this analyzer. "
            f"Available: {available}"
        )


    def rank_countries_by_skill(
        self,
        skill_category: str,
        year: int,
        top_n: int = 10,
    ) -> pd.DataFrame:
        """
        Rank countries by mean ICT skill proficiency for a given category and year,
        returning the top and bottom performers. Only total-population rows are used.

        Parameters:
            skill_category (str): One of the managed skill categories.
            year (int): Data year to filter on.
            top_n (int): Number of top and bottom countries to return. Defaults to 10.
        Returns:
            DataFrame: Columns entityName, entityIso, and mean_value sorted descending.
        Raises:
            ValueError: If skill_category is not loaded, year is not in the dataset,
                        or top_n is less than 1.
        """
        if top_n < 1:
            raise ValueError("top_n must be a positive integer.")

        ds = self._get_dataset(skill_category)
        year_df = ds.filter_by_year(year)
        # Restrict to total-population rows only
        year_totals = year_df[year_df["seriesParent"].isna()]

        ranked = (
            year_totals
            .groupby(["entityIso", "entityName"], as_index=False)["dataValue"]
            .mean()
            .rename(columns={"dataValue": "mean_value"})
            .sort_values("mean_value", ascending=False)
        )
        ranked["mean_value"] = ranked["mean_value"].round(2)

        # Return top_n from each end (top performers + bottom performers)
        top = ranked.head(top_n)
        bottom = ranked.tail(top_n)
        return pd.concat([top, bottom]).drop_duplicates().reset_index(drop=True)

    def identify_skill_gaps(self, threshold: float = 50.0) -> list:
        """
        Identify countries whose mean ICT skill rate falls below a threshold
        across all managed skill categories.

        Parameters:
            threshold (float): Percentage threshold (0-100). Defaults to 50.0.
        Returns:
            list: Sorted list of country ISO codes below the threshold.
        Raises:
            ValueError: If threshold is outside the range 0-100.
        """
        if not (0.0 <= threshold <= 100.0):
            raise ValueError("threshold must be between 0 and 100.")

        combined = self._get_combined_totals()
        # Compute mean dataValue per country across all categories
        country_means = (
            combined
            .groupby("entityIso")["dataValue"]
            .mean()
        )
        # Use a list comprehension to build the gap list (Part 2 requirement P2.2)
        gap_countries = [
            iso for iso, mean_val in country_means.items()
            if mean_val < threshold
        ]
        return sorted(gap_countries)

    def compare_skill_categories(
        self,
        country_iso: str,
        year: int | None = None,
    ) -> dict:
        """
        Compare mean ICT skill proficiency across all managed categories for a country.

        Parameters:
            country_iso (str): country code (e.g. "CAN").
            year (int | None): Optional year filter. If None, all years are averaged.
        Returns:
            dict: Maps skill category name to mean proficiency percentage.
        Raises:
            ValueError: If country_iso is not found in any dataset.
        """
        result = {}
        found = False

        for ds in self.datasets:
            if country_iso.upper() not in ds.available_countries:
                continue
            found = True
            country_df = ds.filter_by_country(country_iso)
            # Keep only total-population rows
            country_df = country_df[country_df["seriesParent"].isna()]
            if year is not None:
                country_df = country_df[country_df["dataYear"] == year]
            if not country_df.empty:
                result[ds.skill_category] = round(
                    country_df["dataValue"].astype(float).mean(), 2
                ).item()

        if not found:
            raise ValueError(
                f"Country ISO '{country_iso}' was not found in any loaded dataset."
            )
        return result

    def analyze_skill_trends(self, country_iso: str) -> pd.DataFrame:
        """
        Analyze ICT skill proficiency trends over time for a given country
        across all managed skill categories.

        Parameters:
            country_iso (str): country code.
        Returns:
            DataFrame: Columns dataYear, skill_category, and mean_value.
        Raises:
            ValueError: If country_iso is not found in any dataset.
        """
        frames = []
        found = False

        for ds in self.datasets:
            if country_iso.upper() not in ds.available_countries:
                continue
            found = True
            country_df = ds.filter_by_country(country_iso)
            country_df = country_df[country_df["seriesParent"].isna()]
            trend = (
                country_df
                .groupby("dataYear", as_index=False)["dataValue"]
                .mean()
                .rename(columns={"dataValue": "mean_value"})
            )
            trend["skill_category"] = ds.skill_category
            frames.append(trend)

        if not found:
            raise ValueError(
                f"Country ISO '{country_iso}' was not found in any loaded dataset."
            )
        return pd.concat(frames, ignore_index=True).sort_values("dataYear")

    def analyze_gender_gap(self, country_iso: str) -> pd.DataFrame:
        """
        Compare male vs. female ICT skill proficiency across all managed
        skill categories for a given country.

        Parameters:
            country_iso (str): country code (e.g. "CAN").
        Returns:
            DataFrame: Columns skill_category, male_mean, female_mean, and gap.
        Raises:
            ValueError: If no gender-disaggregated data is found for the country.
        """
        rows = []
        for ds in self.datasets:
            if country_iso.upper() not in ds.available_countries:
                continue

            male_df = ds.get_by_gender("male")
            female_df = ds.get_by_gender("female")

            iso_upper = country_iso.upper()
            male_country = male_df[male_df["entityIso"] == iso_upper]["dataValue"]
            female_country = female_df[female_df["entityIso"] == iso_upper]["dataValue"]

            if male_country.empty or female_country.empty:
                continue

            male_mean = round(male_country.astype(float).mean(), 2)
            female_mean = round(female_country.astype(float).mean(), 2)
            rows.append({
                "skill_category": ds.skill_category,
                "male_mean":      male_mean,
                "female_mean":    female_mean,
                "gap":            round(male_mean - female_mean, 2),
            })

        if not rows:
            raise ValueError(
                f"No gender-disaggregated data found for '{country_iso}' "
                "in any loaded dataset."
            )
        return pd.DataFrame(rows)

    def analyze_age_group_distribution(
        self,
        country_iso: str,
        age_bands: tuple = ("15to24", "25to34", "35to44", "45to54", "55to64", "65andOver"),
    ) -> pd.DataFrame:
        """
        Analyze ICT skill proficiency across age groups for a given country.

        Age bands use the ITU naming convention embedded in seriesCode (e.g. HHC15to24).

        Parameters:
            country_iso (str): country code (e.g. "CAN").
            age_bands (tuple): Age-band label strings to query. Defaults to standard ITU bands.
        Returns:
            DataFrame: Columns skill_category, age_band, and mean_value.
        Raises:
            ValueError: If no age-disaggregated data is found for the country.
        """
        # age_bands is an immutable tuple (satisfies P1.7 immutable type requirement)
        rows = []
        iso_upper = country_iso.upper()

        for ds in self.datasets:
            for band in age_bands:
                band_df = ds.get_by_age_group(band)
                country_band = band_df[band_df["entityIso"] == iso_upper]["dataValue"]
                if country_band.empty:
                    continue
                rows.append({
                    "skill_category": ds.skill_category,
                    "age_band":       band,
                    "mean_value":     round(country_band.astype(float).mean(), 2),
                })

        if not rows:
            raise ValueError(
                f"No age-disaggregated data found for '{country_iso}' "
                "in any loaded dataset."
            )
        return pd.DataFrame(rows)


    def plot_global_skill_distribution(self, year: int) -> matplotlib.figure.Figure:
        """
        Plot a side-by-side bar chart of the top-10 and bottom-10 countries by mean
        ICT skill proficiency across all loaded categories for a given year.

        Parameters:
            year (int): Data year to visualize.
        Returns:
            Figure: matplotlib Figure object.
        Raises:
            ValueError: If no data exists for the given year.
        """
        combined = self._get_combined_totals()
        year_df = combined[combined["dataYear"] == year]

        if year_df.empty:
            raise ValueError(f"No data found for year {year}.")

        country_means = (
            year_df
            .groupby(["entityIso", "entityName"], as_index=False)["dataValue"]
            .mean()
            .rename(columns={"dataValue": "mean_value"})
            .sort_values("mean_value", ascending=False)
        )

        top10 = country_means.head(10)
        bot10 = country_means.tail(10).sort_values("mean_value")

        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle(
            f"Global ICT Skills Distribution — Top & Bottom 10 Countries ({year})",
            fontsize=14,
            fontweight="bold",
        )

        # Top 10
        axes[0].barh(top10["entityName"], top10["mean_value"], color="steelblue")
        axes[0].set_xlabel("Mean Skill Proficiency (%)")
        axes[0].set_title("Top 10 Countries")
        axes[0].xaxis.set_major_formatter(mticker.PercentFormatter(xmax=100))
        axes[0].invert_yaxis()

        # Bottom 10
        axes[1].barh(bot10["entityName"], bot10["mean_value"], color="tomato")
        axes[1].set_xlabel("Mean Skill Proficiency (%)")
        axes[1].set_title("Bottom 10 Countries")
        axes[1].xaxis.set_major_formatter(mticker.PercentFormatter(xmax=100))
        axes[1].invert_yaxis()

        plt.tight_layout()
        return fig

    def plot_skill_category_comparison(
        self,
        countries_list: list,
        year: int | None = None,
    ) -> matplotlib.figure.Figure:
        """
        Plot a grouped horizontal bar chart comparing mean ICT skill
        proficiency across all loaded categories for a set of countries.

        Parameters:
            countries_list (list): List of ISO 3166-1 alpha-3 country codes.
            year (int | None): Optional year filter. If None, all years are averaged.
        Returns:
            Figure: matplotlib Figure object.
        Raises:
            ValueError: If countries_list is empty or no data is found.
        """
        if not countries_list:
            raise ValueError("countries_list must not be empty.")

        records = []
        for iso in countries_list:
            cat_means = self.compare_skill_categories(iso, year=year)
            for cat, mean_val in cat_means.items():
                records.append({"country": iso, "category": cat, "mean_value": mean_val})

        if not records:
            raise ValueError("No data found for the given countries and year.")

        plot_df = pd.DataFrame(records)
        pivot = plot_df.pivot(index="category", columns="country", values="mean_value")

        fig, ax = plt.subplots(figsize=(12, max(5, len(pivot) * 0.9)))
        pivot.plot(kind="barh", ax=ax)

        title_year = f" ({year})" if year else ""
        ax.set_title(
            f"ICT Skill Category Comparison by Country{title_year}",
            fontsize=13,
            fontweight="bold",
        )
        ax.set_xlabel("Mean Skill Proficiency (%)")
        ax.xaxis.set_major_formatter(mticker.PercentFormatter(xmax=100))
        ax.legend(title="Country", bbox_to_anchor=(1.01, 1), loc="upper left")
        plt.tight_layout()
        return fig

    def plot_gender_gap(
        self,
        countries_list: list,
        skill_category: str,
    ) -> matplotlib.figure.Figure:
        """
        Plot a grouped bar chart of male vs. female ICT skill proficiency for
        a set of countries within a specific skill category.

        Parameters:
            countries_list (list): List of ISO 3166-1 alpha-3 country codes.
            skill_category (str): The skill category to visualize.
        Returns:
            Figure: matplotlib Figure object.
        Raises:
            ValueError: If no gender data is found for any of the given countries.
        """
        if not countries_list:
            raise ValueError("countries_list must not be empty.")

        ds = self._get_dataset(skill_category)
        male_df = ds.get_by_gender("male")
        female_df = ds.get_by_gender("female")

        records = []
        for iso in countries_list:
            iso_upper = iso.upper()
            m = male_df[male_df["entityIso"] == iso_upper]["dataValue"]
            f = female_df[female_df["entityIso"] == iso_upper]["dataValue"]
            if m.empty or f.empty:
                continue
            records.append({
                "country":     iso_upper,
                "Male":        round(m.astype(float).mean(), 2),
                "Female":      round(f.astype(float).mean(), 2),
            })

        if not records:
            raise ValueError(
                f"No gender data found for the given countries in '{skill_category}'."
            )

        plot_df = pd.DataFrame(records).set_index("country")
        x = np.arange(len(plot_df))
        width = 0.35

        fig, ax = plt.subplots(figsize=(max(8, len(plot_df) * 1.2), 5))
        ax.bar(x - width / 2, plot_df["Male"],   width, label="Male",   color="steelblue")
        ax.bar(x + width / 2, plot_df["Female"], width, label="Female", color="salmon")

        ax.set_title(
            f"Gender Gap in ICT Skills: {skill_category.replace('-', ' ').title()}",
            fontsize=13,
            fontweight="bold",
        )
        ax.set_ylabel("Mean Skill Proficiency (%)")
        ax.set_xticks(x)
        ax.set_xticklabels(plot_df.index, rotation=45, ha="right")
        ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=100))
        ax.legend()
        plt.tight_layout()
        return fig


if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from digital_skills.ict_skills_dataset import ICTSkillsDataset

    print("=== DigitalSkillsAnalyzer smoke test ===\n")
    ds_safety = ICTSkillsDataset("safety")
    ds_problem = ICTSkillsDataset("problem-solving")
    analyzer = DigitalSkillsAnalyzer([ds_safety, ds_problem])
    print(analyzer)

    print("\nRanking countries by safety skills in 2023:")
    print(analyzer.rank_countries_by_skill("safety", 2023, top_n=5))

    print("\nSkill gaps (below 30%):", analyzer.identify_skill_gaps(threshold=30.0)[:5])
    print("\nCompare categories for Canada:", analyzer.compare_skill_categories("CAN"))

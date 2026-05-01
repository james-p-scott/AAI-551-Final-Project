"""
digital_skills_analysis.py

Top-level entry-point functions for the Digital Literacy & ICT Skills analysis
module. These functions are called to load datasets, run analysis, and generate visualizations.
"""

import os
import sys

import pandas as pd

# Ensure the project root is on sys.path so file_io.py can be imported.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import file_io
from digital_skills.ict_skills_dataset import ICTSkillsDataset, SKILL_CATEGORY_FILES
from digital_skills.digital_skills_analyzer import DigitalSkillsAnalyzer 

_SKILL_LEVEL_CSV = "individuals-with-ict-skills-by-skill-level.csv"


def load_all_ict_skill_datasets() -> list:
    """
    Load all five ITU ICT skill-category CSVs and return a list of
    ICTSkillsDataset instances.

    Uses a list comprehension to construct all five datasets in a single expression.

    Returns:
        list: Five ICTSkillsDataset instances, one per skill category.
    """
    # list comprehension over all recognised category keys (P2.2)
    datasets = [
        ICTSkillsDataset(category)
        for category in SKILL_CATEGORY_FILES.keys()
    ]
    return datasets


def load_skill_level_summary() -> pd.DataFrame | None:
    """
    Load the ITU by-skill-level aggregate CSV as a plain pandas DataFrame.
    This CSV provides basic vs. above-basic skill-level breakdowns and is
    used for a high-level overview only — it has no demographic breakdowns.
    Returns:
        DataFrame: The skill-level summary, or None if loading fails.
    """
    datasets_dir = os.path.join(_PROJECT_ROOT, "datasets")
    loader = file_io.CSV_Load_DF(datasets_dir, _SKILL_LEVEL_CSV)
    return loader.df


def iter_country_data(df: pd.DataFrame):
    """
    Generator that yields all rows for each unique country in a DataFrame,
    one country at a time.
    Parameters:
        df (DataFrame): Source DataFrame containing an entityIso column.
    Yields:
        tuple: (iso_code (str), country_df (DataFrame)) for each unique country.
    Raises:
        ValueError: If df does not contain an entityIso column.
    """
    if "entityIso" not in df.columns:
        raise ValueError("DataFrame must contain an 'entityIso' column.")

    for iso in df["entityIso"].dropna().unique():
        yield iso, df[df["entityIso"] == iso].copy()


def run_digital_literacy_analysis() -> dict:
    """
    Orchestrate the full Digital Literacy & ICT Skills analysis pipeline.
    Loads all five ICT skill datasets, computes summary statistics, identifies
    skill gap countries, and returns the results for use in the project notebook.
    Returns:
        dict: Analysis results keyed by analyzer, datasets, summary_df,
              stats_results, and gap_countries.
    """
    print("=" * 60)
    print("Digital Literacy & ICT Skills Analysis")
    print("AAI-551 Final Project — Digital Divide")
    print("=" * 60)

    # Step 1: Load datasets
    print("\n[1/4] Loading ICT skill-category datasets...")
    datasets = load_all_ict_skill_datasets()
    analyzer = DigitalSkillsAnalyzer(datasets)
    print(analyzer)

    # Step 2: Skill-level overview
    print("\n[2/4] Loading skill-level summary...")
    summary_df = load_skill_level_summary()
    if summary_df is not None:
        print(f"Skill-level summary loaded: {len(summary_df):,} rows")

    # Step 3: Summary statistics per category
    print("\n[3/4] Summary statistics per skill category:")
    stats_results = {}
    for ds in datasets:
        stats = ds.get_summary_stats()
        stats_results[ds.skill_category] = stats
        print(
            f"{ds.skill_category:<40} "
            f"n={stats['count']:>4}  "
            f"mean={stats['mean']:>6.2f}%  "
            f"median={stats['median']:>6.2f}%"
        )

    # Step 4: Identify skill gaps
    print("\n[4/4] Identifying ICT skill gaps (mean < 40% across all categories)...")
    gap_countries = analyzer.identify_skill_gaps(threshold=40.0)
    print(f"{len(gap_countries)} countries identified with skill gaps.")
    if gap_countries:
        print(f"  Example: {gap_countries[:8]}")

    results = {
        "analyzer":      analyzer,
        "datasets":      datasets,
        "summary_df":    summary_df,
        "stats_results": stats_results,
        "gap_countries": gap_countries,
    }

    print("\nAnalysis complete. Call individual analyzer methods or")
    print("visualization functions to explore results further.")
    print("=" * 60)

    return results


if __name__ == "__main__":
    results = run_digital_literacy_analysis()
    print(f"\nLoaded {len(results['datasets'])} datasets.")
    print(f"Gap countries (first 10): {results['gap_countries'][:10]}")

    # Demonstrate the generator
    first_ds = results["datasets"][0]
    totals = first_ds.get_totals()
    print("\nIterating first 3 countries via generator:")
    count = 0
    for iso, country_df in iter_country_data(totals):
        print(f"  {iso}: {len(country_df)} rows")
        count += 1
        if count >= 3:
            break

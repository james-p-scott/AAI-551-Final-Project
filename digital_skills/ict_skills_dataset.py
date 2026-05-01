"""
ict_skills_dataset.py

Loads a single ITU ICT skill-category CSV and exposes filtered views of the
data by demographic breakdown (gender, age group, and urban/rural geography).

Each ITU ICT skills CSV contains two logical row types, distinguished by
the seriesParent column:
  - Total rows: seriesParent is NaN, representing the full population aggregate
  - Breakdown rows: seriesParent is non-NaN, linked to a total row via suffixes
                    such as HHCMale, HHCFemale, HHC15to24, HHCUrbanUsers, etc.
"""

import os
import sys
import statistics

import pandas as pd


# Ensure the project root (parent of this package) is on sys.path so that
# file_io.py can be imported regardless of the working directory the caller uses.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import file_io

# Maps human-readable skill category names to their ITU dataset filenames.
SKILL_CATEGORY_FILES = {
    "information-and-data-literacy":     "individuals-with-ict-skills-information-and-data-literacy.csv",
    "communication-and-collaboration":   "individuals-with-ict-skills-communication-and-collaboration.csv",
    "digital-content-creation":          "individuals-with-ict-skills-digital-content-creation.csv",
    "problem-solving":                   "individuals-with-ict-skills-problem-solving.csv",
    "safety":                            "individuals-with-ict-skills-safety.csv",
}

# seriesCode substring patterns used to identify demographic breakdown rows.
_GENDER_MAP = {
    "male":   "HHCMale",
    "female": "HHCFemale",
}

_LOCATION_MAP = {
    "urban": "HHCUrbanUsers",
    "rural": "HHCRuralUsers",
}


class ICTSkillsDataset:
    """
    Loads and wraps one ITU ICT skill-category CSV as a pandas DataFrame,
    providing filtered views by country, year, gender, age group, and
    urban/rural geography.

    Demonstrates composition by using file_io.CSV_Load_DF to perform the
    actual CSV load.
    """

    def __init__(self, skill_category: str):
        """
        Construct an ICTSkillsDataset for the given skill category.
        Parameters:
            skill_category (str): One of the recognised ITU skill category names.
        Raises:
            ValueError: If skill_category is not a valid key in SKILL_CATEGORY_FILES.
        """
        # Validate the category name before attempting any I/O
        if skill_category not in SKILL_CATEGORY_FILES:
            valid = ", ".join(sorted(SKILL_CATEGORY_FILES.keys()))
            raise ValueError(
                f"Unknown skill category '{skill_category}'. "
                f"Valid categories are: {valid}"
            )

        # Store as an immutable string attribute
        self.skill_category: str = skill_category

        # Build the absolute path to the datasets/ directory so this class
        # works regardless of the working directory the caller uses.
        datasets_dir = os.path.join(_PROJECT_ROOT, "datasets")
        filename = SKILL_CATEGORY_FILES[skill_category]

        # Compose with teammate's CSV_Load_DF class to perform the actual load
        _loader = file_io.CSV_Load_DF(datasets_dir, filename)
        self.df: pd.DataFrame | None = _loader.df

        # Build convenience index lists (mutable) from the loaded data
        if self.df is not None:
            self.available_countries: list = sorted(
                self.df["entityIso"].dropna().unique().tolist()
            )
            self.available_years: list = sorted(
                self.df["dataYear"].dropna().unique().astype(int).tolist()
            )
        else:
            self.available_countries = []
            self.available_years = []

    def __str__(self) -> str:
        """
        Return a human-readable summary of this dataset instance.
        Returns:
            str: Multi-line string showing category, row count, country count, and year range.
        """
        if self.df is None:
            return f"ICTSkillsDataset('{self.skill_category}') — data not loaded"

        year_range = (
            f"{min(self.available_years)}–{max(self.available_years)}"
            if self.available_years else "N/A"
        )
        return (
            f"ICTSkillsDataset\n"
            f"  Category : {self.skill_category}\n"
            f"  Rows     : {len(self.df):,}\n"
            f"  Countries: {len(self.available_countries)}\n"
            f"  Years    : {year_range}"
        )

    def __len__(self) -> int:
        """
        Return the total number of rows in the loaded DataFrame.
        Returns:
            int: Row count, or 0 if data is not loaded.
        """
        if self.df is None:
            return 0
        return len(self.df)

    def get_totals(self) -> pd.DataFrame:
        """
        Return only the total-population rows where seriesParent is NaN.
        Returns:
            DataFrame: Rows representing the full population aggregate only.
        Raises:
            RuntimeError: If the dataset was not loaded successfully.
        """
        self._require_loaded()
        # Total rows have no parent — seriesParent is NaN in the loaded df
        return self.df[self.df["seriesParent"].isna()].copy()

    def get_by_gender(self, gender: str) -> pd.DataFrame:
        """
        Return rows for the specified gender demographic breakdown.
        Parameters:
            gender (str): "male" or "female" (case-insensitive).
        Returns:
            DataFrame: Rows filtered to the requested gender.
        Raises:
            ValueError: If gender is not "male" or "female".
            RuntimeError: If the dataset was not loaded successfully.
        """
        self._require_loaded()
        key = gender.lower()
        if key not in _GENDER_MAP:
            raise ValueError(
                f"Invalid gender '{gender}'. Must be 'male' or 'female'."
            )
        pattern = _GENDER_MAP[key]
        return self.df[self.df["seriesCode"].str.contains(pattern, na=False)].copy()

    def get_by_age_group(self, age_band: str) -> pd.DataFrame:
        """
        Return rows for a specific ITU age-band code.
        The ITU encodes age groups as substrings in seriesCode (e.g. HHC15to24).
        Parameters:
            age_band (str): Age-band substring to match inside seriesCode (e.g. "15to24").
        Returns:
            DataFrame: Rows filtered to the requested age band.
        Raises:
            ValueError: If age_band is an empty string.
            RuntimeError: If the dataset was not loaded successfully.
        """
        self._require_loaded()
        if not age_band or not age_band.strip():
            raise ValueError("age_band must be a non-empty string.")
        # Build the full ITU pattern used in seriesCode
        pattern = f"HHC{age_band}"
        matches = self.df[self.df["seriesCode"].str.contains(pattern, na=False)]
        if matches.empty:
            # Inform the caller but return an empty df rather than raising,
            # since not every dataset covers every age band.
            print(f"Warning: No rows found for age band '{age_band}' "
                  f"in category '{self.skill_category}'.")
        return matches.copy()

    def get_by_urban_rural(self, location: str) -> pd.DataFrame:
        """
        Return rows for the urban or rural geographic breakdown.
        Parameters:
            location (str): "urban" or "rural" (case-insensitive).
        Returns:
            DataFrame: Rows filtered to the requested location type.
        Raises:
            ValueError: If location is not "urban" or "rural".
            RuntimeError: If the dataset was not loaded successfully.
        """
        self._require_loaded()
        key = location.lower()
        if key not in _LOCATION_MAP:
            raise ValueError(
                f"Invalid location '{location}'. Must be 'urban' or 'rural'."
            )
        pattern = _LOCATION_MAP[key]
        return self.df[self.df["seriesCode"].str.contains(pattern, na=False)].copy()

    def filter_by_country(self, iso: str) -> pd.DataFrame:
        """
        Return all rows for a specific country ISO code.
        Parameters:
            iso (str): Three-letter country code (e.g. "CAN").
        Returns:
            DataFrame: All rows for the given country.
        Raises:
            ValueError: If iso is not present in the dataset.
            RuntimeError: If the dataset was not loaded successfully.
        """
        self._require_loaded()
        iso_upper = iso.upper()
        if iso_upper not in self.available_countries:
            raise ValueError(
                f"Country ISO '{iso}' not found in dataset. "
                f"Use available_countries to see valid codes."
            )
        return self.df[self.df["entityIso"] == iso_upper].copy()

    def filter_by_year(self, year: int) -> pd.DataFrame:
        """
        Return all rows for a specific data year.
        Parameters:
            year (int): Four-digit calendar year (e.g. 2022).
        Returns:
            DataFrame: All rows for the given year.
        Raises:
            ValueError: If year is not present in the dataset.
            RuntimeError: If the dataset was not loaded successfully.
        """
        self._require_loaded()
        if year not in self.available_years:
            raise ValueError(
                f"Year {year} not found in dataset. "
                f"Use available_years to see valid years."
            )
        return self.df[self.df["dataYear"] == year].copy()

    def get_summary_stats(self) -> dict:
        """
        Compute descriptive statistics for the total-population dataValue column.
        Only total-population rows are included so demographic sub-groups do not
        skew the aggregate figures. Uses the built-in statistics module.
        Returns:
            dict: Keys are mean, median, stdev, min, max, count, and category.
        Raises:
            RuntimeError: If the dataset was not loaded successfully.
        """
        self._require_loaded()
        values = (
            self.get_totals()["dataValue"]
            .dropna()
            .astype(float)
            .tolist()
        )

        if len(values) < 2:
            return {
                "category": self.skill_category,
                "count": len(values),
                "mean": values[0] if values else None,
                "median": values[0] if values else None,
                "stdev": 0.0,
                "min": values[0] if values else None,
                "max": values[0] if values else None,
            }

        # Use the built-in statistics module (Part 2 requirement P2.3)
        return {
            "category": self.skill_category,
            "count":    len(values),
            "mean":     round(statistics.mean(values), 4),
            "median":   round(statistics.median(values), 4),
            "stdev":    round(statistics.stdev(values), 4),
            "min":      round(min(values), 4),
            "max":      round(max(values), 4),
        }

    def _require_loaded(self):
        """
        Raise RuntimeError if the DataFrame was not loaded successfully.
        Raises:
            RuntimeError: If self.df is None.
        """
        if self.df is None:
            raise RuntimeError(
                f"Data for category '{self.skill_category}' is not loaded. "
                "Check that the datasets/ directory exists and the CSV file "
                "is present."
            )

if __name__ == "__main__":
    # Smoke test — loads the 'safety' category and prints a summary.
    print("ICTSkillsDataset smoke test\n")
    ds = ICTSkillsDataset("safety")
    print(ds)
    print(f"\nSummary stats: {ds.get_summary_stats()}")
    print(f"\nFirst 3 total rows:\n{ds.get_totals().head(3)}")
    print(f"\nFirst 3 male rows:\n{ds.get_by_gender('male').head(3)}")

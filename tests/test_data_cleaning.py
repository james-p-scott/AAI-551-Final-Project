"""
unit test cases used to validate the data cleaning behavior from file_io.py and
global_internet_access.py

these unit tests construct Pandas dataframes in memory and loads them into a loader using
the file_io.CSV_Load_DF instance (since the Clean_DF class expects an instance of
CSV_Load_DF.

the following 2 unit tests are implemented:
  1.  test_reduce_to_core_columns_preserves_order_and_coercion:
          validates that Clean_DF.reduce_to_core_columns maintains core-column order,
          drops non-core columns, and coerces dataValue to numeric
  2.  test_reduce_to_latest_by_iso_keeps_most_recent_valid_value:
          validates that Clean_DF.reduce_to_latest_by_iso keeps only the most recent row
          per ISO indexed rows having valid dataValue, discarding invalid or missing
          dataValue entries
"""
# import the external libs used
import pandas as pd
import pytest

# import the classes and functions defined in file_io.py
import file_io


def make_loader_with_df(df):
    """
    helper function: create a CSV_Load_DF instance and inject the Pandas dataframe into its
    `.df`.  pass a non-existing filename so that CSV_Load_DF.__init__ executes before we then
    overwrite `.df` with our in-memory df
    """
    loader = file_io.CSV_Load_DF("datasets", "nonexistent-for-tests.csv")

    # write our test df into our in-memory df
    loader.df = df.copy()

    # return the in-memory df
    return loader


def test_reduce_to_core_columns_preserves_order_and_coercion():
    """
    create a DataFrame that contains the core columns (plus extra columns) and ensure
    reduce_to_core_columns:
      - keeps only the core columns (in the CORE_COLUMNS order)
      - coerces dataValue to numeric dtype (NaN for non-numeric)
    """
    # Build an input DataFrame with core columns in arbitrary order and an extra column
    input_df = pd.DataFrame({
        "entityIso": ["ABC", "DEF"],
        "seriesName": ["s1", "s1"],
        "dataValue": ["10.0", "not-a-number"],
        "dataYear": ["2026", "2020"],
        "extraCol": ["x", "y"],
        "seriesUnits": ["pct", "pct"],
        "entityID": [1, 2],
    })
    loader = make_loader_with_df(input_df)

    cleaner = file_io.Clean_DF(loader=loader)

    # call the method under test
    out_df = cleaner.reduce_to_core_columns()

    # expected available columns are the CORE_COLUMNS in their defined order
    expected_order = file_io.Clean_DF.CORE_COLUMNS
    assert list(out_df.columns) == expected_order, "Core columns should be kept in canonical order"

    # remove 'extraCol'
    assert "extraCol" not in out_df.columns

    # dataValue should be coerced to numeric: first row numeric, second becomes NaN
    assert pd.api.types.is_numeric_dtype(out_df["dataValue"]), "dataValue must be numeric after coercion"
    assert pd.notna(out_df.loc[0, "dataValue"]), "first row should have numeric dataValue"
    assert pd.isna(out_df.loc[1, "dataValue"]), "non-numeric dataValue should be coerced to NaN"

def test_reduce_to_latest_by_iso_keeps_most_recent_valid_value():
    """
    create a DataFrame with multiple rows per ISO where some rows have missing or NaN dataValue
    and ensure reduce_to_latest_by_iso keeps the most recent row (by dataYear) that has a valid dataValue.
    """
    # Build input DataFrame with duplicates for some ISOs so the reducer has to choose the most recent valid
    input_df = pd.DataFrame({
        # ABC appears twice: 2020 has NaN, 2021 has a valid "0.90" -> should keep 2021 for ABC
        # DEF appears twice: 2020 has NaN, 2019 had valid earlier in original example; here we provide
        # a single valid row at 2021 with 0.25 so it will be kept.
        # GHI appears only once and is valid.
        "entityIso": ["ABC", "ABC", "DEF", "GHI", "MNO"],
        "dataYear": [2020, 2021, 2021, 2022, 2024],
        "dataValue": [pd.NA, "0.90", "0.25", "0.25", "0.333"],
        "seriesName": ["s", "s", "s", "s", "s"],
        "seriesUnits": ["frac", "frac", "frac", "frac", "frac"],
        "entityID": [10, 10, 20, 30, 50],
    })

    loader = make_loader_with_df(input_df)
    cleaner = file_io.Clean_DF(loader=loader)

    # precondition: reduce to core columns first (as the pipeline expects)
    cleaner.reduce_to_core_columns()

    # call reduce_to_latest_by_iso and inspect the results
    reduced = cleaner.reduce_to_latest_by_iso()

    # keep one row per ISO: ABC, DEF, GHI, MNO
    kept_isos = set(reduced["entityIso"].astype(str).tolist())
    # We expect ABC to be present now because 2021 for ABC has a valid value "0.90"
    assert kept_isos == {"ABC", "DEF", "GHI", "MNO"}

    # for ABC, most recent valid is 2021 with dataValue 0.90
    abc_row = reduced[reduced["entityIso"] == "ABC"].iloc[0]
    assert int(abc_row["dataYear"]) == 2021
    # dataValue should be numeric and approximately 0.90
    assert float(abc_row["dataValue"]) == pytest.approx(0.90)

    # For DEF, keep the single valid row at 2021 with 0.25
    def_row = reduced[reduced["entityIso"] == "DEF"].iloc[0]
    assert int(def_row["dataYear"]) == 2021
    assert float(def_row["dataValue"]) == pytest.approx(0.25)

    # For GHI, only one row exists
    ghi_row = reduced[reduced["entityIso"] == "GHI"].iloc[0]
    assert int(ghi_row["dataYear"]) == 2022
    assert float(ghi_row["dataValue"]) == pytest.approx(0.25)

    # For MNO single valid row
    mno_row = reduced[reduced["entityIso"] == "MNO"].iloc[0]
    assert int(mno_row["dataYear"]) == 2024
    assert float(mno_row["dataValue"]) == pytest.approx(0.333)

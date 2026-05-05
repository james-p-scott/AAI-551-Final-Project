import pandas as pd
import pytest

from price_regulation.price_regulation_dataset import PriceRegulationDataset


def make_sample_files(tmp_path):
    """make sample csv files for testing"""
    price_data = pd.DataFrame({  # sample price data
        "seriesName": [
            "Price regulation of retail Internet access and data services",
            "Price regulation of retail Internet access and data services",
            "Price regulation of retail Internet access and data services",
            "Price regulation of retail voice services",
        ],
        "entityIso": ["AAA", "AAA", "BBB", "AAA"],
        "entityName": ["Country A", "Country A", "Country B", "Country A"],
        "dataValue": ["Without price control", "With price control", "Without price control", "With price control"],
        "dataYear": [2020, 2024, 2024, 2024],
    })

    internet_data = pd.DataFrame({  # sample internet data
        "entityIso": ["AAA", "AAA", "BBB"],
        "entityName": ["Country A", "Country A", "Country B"],
        "dataValue": [70.0, 80.0, 45.0],
        "dataYear": [2020, 2024, 2024],
    })

    price_data.to_csv(tmp_path / "price.csv", index=False)  # save price csv
    internet_data.to_csv(tmp_path / "internet.csv", index=False)  # save internet csv


def test_clean_price_data_filters_target_series(tmp_path):
    """check that only the target series is kept"""
    make_sample_files(tmp_path)  # make test files
    dataset = PriceRegulationDataset("price.csv", "internet.csv", data_dir=tmp_path)
    df = dataset.clean_price_data()  # clean price data

    assert df["seriesName"].nunique() == 1
    assert len(df) == 3


def test_latest_price_by_country_keeps_latest_year(tmp_path):
    """check that the latest country year is kept"""
    make_sample_files(tmp_path)  # make test files
    dataset = PriceRegulationDataset("price.csv", "internet.csv", data_dir=tmp_path)
    latest = dataset.latest_price_by_country()  # get latest data

    row = latest[latest["entityIso"] == "AAA"].iloc[0]  # get country row
    assert row["dataYear"] == 2024
    assert row["price_control"] == 1


def test_merge_with_internet_usage(tmp_path):
    """check that price data merges with internet usage"""
    make_sample_files(tmp_path)  # make test files
    dataset = PriceRegulationDataset("price.csv", "internet.csv", data_dir=tmp_path)
    merged = dataset.merge_with_internet_usage()  # merge datasets

    assert "internet_usage" in merged.columns
    assert len(merged) == 2


def test_filter_by_country_returns_rows(tmp_path):
    """check that filtering by country returns rows"""
    make_sample_files(tmp_path)  # make test files
    dataset = PriceRegulationDataset("price.csv", "internet.csv", data_dir=tmp_path)
    result = dataset.filter_by_country("AAA")  # filter country

    assert len(result) == 2


def test_filter_by_bad_country_raises_error(tmp_path):
    """check that a bad country raises an error"""
    make_sample_files(tmp_path)  # make test files
    dataset = PriceRegulationDataset("price.csv", "internet.csv", data_dir=tmp_path)

    with pytest.raises(ValueError):  # expect error
        dataset.filter_by_country("XXX")

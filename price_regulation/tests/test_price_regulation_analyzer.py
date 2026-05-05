import pandas as pd
import pytest

from price_regulation.price_regulation_dataset import PriceRegulationDataset
from price_regulation.price_regulation_analyzer import PriceRegulationAnalyzer


def make_sample_files(tmp_path):
    """make sample csv files for testing"""
    price_data = pd.DataFrame({  # sample price data
        "seriesName": [
            "Price regulation of retail Internet access and data services",
            "Price regulation of retail Internet access and data services",
            "Price regulation of retail Internet access and data services",
        ],
        "entityIso": ["AAA", "BBB", "CCC"],
        "entityName": ["Country A", "Country B", "Country C"],
        "dataValue": ["With price control", "Without price control", "Without price control"],
        "dataYear": [2024, 2024, 2024],
    })

    internet_data = pd.DataFrame({  # sample internet data
        "entityIso": ["AAA", "BBB", "CCC"],
        "entityName": ["Country A", "Country B", "Country C"],
        "dataValue": [90.0, 50.0, 40.0],
        "dataYear": [2024, 2024, 2024],
    })

    price_data.to_csv(tmp_path / "price.csv", index=False)  # save price csv
    internet_data.to_csv(tmp_path / "internet.csv", index=False)  # save internet csv


def test_summary_stats_returns_dict(tmp_path):
    """check that summary stats returns a dictionary"""
    make_sample_files(tmp_path)  # make test files
    dataset = PriceRegulationDataset("price.csv", "internet.csv", data_dir=tmp_path)
    analyzer = PriceRegulationAnalyzer(dataset)
    stats = analyzer.get_summary_stats()  # get stats

    assert isinstance(stats, dict)
    assert stats["countries_compared"] == 3


def test_low_access_without_control(tmp_path):
    """check that low access countries without control are returned"""
    make_sample_files(tmp_path)  # make test files
    dataset = PriceRegulationDataset("price.csv", "internet.csv", data_dir=tmp_path)
    analyzer = PriceRegulationAnalyzer(dataset)
    result = analyzer.get_low_access_without_control(threshold=60)  # find low access countries

    assert len(result) == 2


def test_bad_threshold_raises_error(tmp_path):
    """check that a bad threshold raises an error"""
    make_sample_files(tmp_path)  # make test files
    dataset = PriceRegulationDataset("price.csv", "internet.csv", data_dir=tmp_path)
    analyzer = PriceRegulationAnalyzer(dataset)

    with pytest.raises(ValueError):  # expect error
        analyzer.get_low_access_without_control(threshold=120)


def test_rank_countries_by_internet_usage(tmp_path):
    """check that countries are ranked by internet usage"""
    make_sample_files(tmp_path)  # make test files
    dataset = PriceRegulationDataset("price.csv", "internet.csv", data_dir=tmp_path)
    analyzer = PriceRegulationAnalyzer(dataset)
    result = analyzer.rank_countries_by_internet_usage(top_n=2)  # rank top countries

    assert len(result) == 2
    assert result.iloc[0]["internet_usage"] >= result.iloc[1]["internet_usage"]


def test_generator_returns_country_rows(tmp_path):
    """check that the generator returns country rows"""
    make_sample_files(tmp_path)  # make test files
    dataset = PriceRegulationDataset("price.csv", "internet.csv", data_dir=tmp_path)
    analyzer = PriceRegulationAnalyzer(dataset)
    rows = list(analyzer.iter_country_results())  # convert generator to list

    assert len(rows) == 3
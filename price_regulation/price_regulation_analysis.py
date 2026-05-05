"""
runs the mobile internet price regulation analysis
"""

from .price_regulation_dataset import PriceRegulationDataset
from .price_regulation_analyzer import PriceRegulationAnalyzer


def run_price_regulation_analysis(
    price_file="mobile-services_1778017040787.csv",
    internet_file="individuals-using-the-internet.csv",
    data_dir="datasets"
):
    """run the full price regulation analysis"""
    print("=" * 60)
    print("Running Mobile Internet Price Regulation Analysis")
    print("=" * 60)

    dataset = PriceRegulationDataset(price_file, internet_file, data_dir)  # create dataset
    dataset.clean_price_data()  # clean price data
    dataset.clean_internet_data()  # clean internet data

    analyzer = PriceRegulationAnalyzer(dataset)  # create analyzer
    stats = analyzer.get_summary_stats()  # get stats
    low_access = analyzer.get_low_access_without_control(threshold=60.0)  # find gap countries

    print(dataset)
    print(analyzer)

    print("\nSummary Statistics:")
    for key, value in stats.items():
        print(f"{key}: {value}")

    print(f"\nLow internet usage countries without price control: {len(low_access)}")

    results = {
        "dataset": dataset,
        "analyzer": analyzer,
        "stats": stats,
        "low_access_without_control": low_access,
    }  # return useful results

    return results


if __name__ == "__main__":
    run_price_regulation_analysis()  # run file directly
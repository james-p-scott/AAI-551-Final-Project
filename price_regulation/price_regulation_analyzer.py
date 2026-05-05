"""
analyzes price regulation and internet usage data
"""

import matplotlib.pyplot as plt
import pandas as pd

from .price_regulation_dataset import PriceRegulationDataset


class PriceRegulationAnalyzer:
    """analyze the relationship between price regulation and internet usage"""

    def __init__(self, dataset):
        """set up the analyzer with the cleaned dataset"""
        if not isinstance(dataset, PriceRegulationDataset):
            raise TypeError("dataset must be a PriceRegulationDataset object")

        self.dataset = dataset  # store dataset object
        self.df = dataset.merge_with_internet_usage()  # merge price and internet data

    def __str__(self):
        """return a simple analyzer summary"""
        return f"PriceRegulationAnalyzer(countries={len(self.df)})"

    def get_summary_stats(self):
        """get summary stats for price control and internet usage"""
        regulated = self.df[self.df["price_control"] == 1]  # countries with control
        unregulated = self.df[self.df["price_control"] == 0]  # countries without control

        stats = {
            "countries_compared": int(len(self.df)),
            "with_price_control": int(len(regulated)),
            "without_price_control": int(len(unregulated)),
            "percent_with_price_control": round(len(regulated) / len(self.df) * 100, 2),
            "avg_internet_with_control": round(float(regulated["internet_usage"].mean()), 2),
            "avg_internet_without_control": round(float(unregulated["internet_usage"].mean()), 2),
        }  # summary values

        stats["average_difference"] = round(
            stats["avg_internet_with_control"] - stats["avg_internet_without_control"], 2
        )  # compare averages

        return stats

    def regulation_counts_by_year(self):
        """count price regulation status by year"""
        if self.dataset.clean_price_df is None:
            self.dataset.clean_price_data()  # clean first

        counts = (
            self.dataset.clean_price_df
            .groupby(["dataYear", "dataValue"])
            .size()
            .reset_index(name="country_count")
        )  # count regulation status by year

        return counts

    def get_low_access_without_control(self, threshold=60.0):
        """find countries with low internet usage and no price control"""
        if threshold < 0 or threshold > 100:
            raise ValueError("threshold must be between 0 and 100")

        result = self.df[
            (self.df["price_control"] == 0) &
            (self.df["internet_usage"] < threshold)
        ].copy()  # find low access and no control

        return result.sort_values("internet_usage").reset_index(drop=True)

    def rank_countries_by_internet_usage(self, top_n=10, lowest=False):
        """rank countries by internet usage"""
        if top_n <= 0:
            raise ValueError("top_n must be greater than 0")

        result = (
            self.df
            .sort_values("internet_usage", ascending=lowest)
            .head(top_n)
            .reset_index(drop=True)
        )  # rank countries

        return result

    def iter_country_results(self):
        """return country results one row at a time"""
        for row in self.df.itertuples(index=False):
            yield row.entityIso, row.entityName, row.dataValue, row.internet_usage  # return one row

    def plot_regulation_counts(self):
        """plot counts for each price regulation status"""
        counts = self.df["dataValue"].value_counts()  # count statuses

        fig, ax = plt.subplots(figsize=(7, 5))
        ax.bar(counts.index, counts.values)
        ax.set_title("Mobile Internet/Data Price Regulation")
        ax.set_xlabel("Regulation Status")
        ax.set_ylabel("Number of Countries")
        plt.tight_layout()

        return fig

    def plot_average_internet_usage(self):
        """plot average internet usage by regulation status"""
        grouped = self.df.groupby("dataValue")["internet_usage"].mean()  # average by group

        fig, ax = plt.subplots(figsize=(7, 5))
        ax.bar(grouped.index, grouped.values)
        ax.set_title("Average Internet Usage by Price Regulation Status")
        ax.set_xlabel("Regulation Status")
        ax.set_ylabel("Average Internet Usage (%)")
        ax.set_ylim(0, 100)
        plt.tight_layout()

        return fig

    def plot_low_access_without_control(self, threshold=60.0, top_n=15):
        """plot low internet usage countries without price control"""
        low_df = self.get_low_access_without_control(threshold).head(top_n)  # get lowest countries

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(low_df["entityName"], low_df["internet_usage"])
        ax.set_title("Low Internet Usage Countries Without Price Control")
        ax.set_xlabel("Country")
        ax.set_ylabel("Internet Usage (%)")
        ax.tick_params(axis="x", rotation=75)
        ax.set_ylim(0, 100)
        plt.tight_layout()

        return fig
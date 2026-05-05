"""
loads and cleans price regulation and internet usage data
"""

import os
import pandas as pd


class PriceRegulationDataset:
    """load and clean price regulation and internet usage data"""

    target_series = "Price regulation of retail Internet access and data services"

    def __init__(self, price_file, internet_file="individuals-using-the-internet.csv", data_dir="datasets"):
        """set up the dataset files and empty dataframes"""
        self.price_file = price_file  # store price file name
        self.internet_file = internet_file  # store internet file name
        self.data_dir = data_dir  # store data folder
        self.price_df = None  # raw price data
        self.internet_df = None  # raw internet data
        self.clean_price_df = None  # cleaned price data
        self.clean_internet_df = None  # cleaned internet data
        self.merged_df = None  # combined data

    def __str__(self):
        """return a simple dataset summary"""
        row_count = 0 if self.clean_price_df is None else len(self.clean_price_df)  # count rows
        return f"PriceRegulationDataset(rows={row_count}, series='{self.target_series}')"

    def __len__(self):
        """return the number of cleaned price rows"""
        if self.clean_price_df is None:
            return 0
        return len(self.clean_price_df)

    def __getattr__(self, name):
        """pass dataframe methods through when possible"""
        if self.clean_price_df is not None and hasattr(self.clean_price_df, name):
            return getattr(self.clean_price_df, name)  # pass pandas calls through
        raise AttributeError(f"{name} was not found")

    def _path(self, filename):
        """build the full file path"""
        return os.path.join(self.data_dir, filename)  # build file path

    def load_price_data(self):
        """load the price regulation csv file"""
        try:
            self.price_df = pd.read_csv(self._path(self.price_file))  # load price data
            return self.price_df
        except FileNotFoundError:
            raise FileNotFoundError(f"Price file was not found: {self.price_file}")  # missing file
        except pd.errors.EmptyDataError:
            raise ValueError("Price file is empty.")  # empty file

    def load_internet_data(self):
        """load the internet usage csv file"""
        try:
            self.internet_df = pd.read_csv(self._path(self.internet_file))  # load internet data
            return self.internet_df
        except FileNotFoundError:
            raise FileNotFoundError(f"Internet file was not found: {self.internet_file}")  # missing file
        except pd.errors.EmptyDataError:
            raise ValueError("Internet file is empty.")  # empty file

    def clean_price_data(self):
        """clean the price regulation data"""
        if self.price_df is None:
            self.load_price_data()  # load first

        needed_cols = ["seriesName", "entityIso", "entityName", "dataValue", "dataYear"]  # needed columns
        missing_cols = [col for col in needed_cols if col not in self.price_df.columns]  # check missing

        if missing_cols:
            raise ValueError(f"Missing columns in price data: {missing_cols}")

        df = self.price_df[needed_cols].copy()  # keep needed columns
        df = df[df["seriesName"] == self.target_series].copy()  # keep internet/data regulation
        df["dataYear"] = pd.to_numeric(df["dataYear"], errors="coerce")  # clean year
        df = df.dropna(subset=["entityIso", "entityName", "dataValue", "dataYear"])  # drop bad rows
        df["dataYear"] = df["dataYear"].astype(int)  # make year integer
        df["price_control"] = df["dataValue"].map({"With price control": 1, "Without price control": 0})  # encode status
        df = df.dropna(subset=["price_control"])  # drop unknown status
        df["price_control"] = df["price_control"].astype(int)  # make flag integer

        self.clean_price_df = df.reset_index(drop=True)  # save cleaned data
        return self.clean_price_df

    def clean_internet_data(self):
        """clean the internet usage data"""
        if self.internet_df is None:
            self.load_internet_data()  # load first

        needed_cols = ["entityIso", "entityName", "dataValue", "dataYear"]  # needed columns
        missing_cols = [col for col in needed_cols if col not in self.internet_df.columns]  # check missing

        if missing_cols:
            raise ValueError(f"Missing columns in internet data: {missing_cols}")

        df = self.internet_df[needed_cols].copy()  # keep needed columns
        df["dataValue"] = pd.to_numeric(df["dataValue"], errors="coerce")  # clean percentage
        df["dataYear"] = pd.to_numeric(df["dataYear"], errors="coerce")  # clean year
        df = df.dropna(subset=["entityIso", "entityName", "dataValue", "dataYear"])  # drop bad rows
        df["dataYear"] = df["dataYear"].astype(int)  # make year integer
        df = df.rename(columns={"dataValue": "internet_usage", "dataYear": "internet_year"})  # clearer names

        self.clean_internet_df = df.reset_index(drop=True)  # save cleaned data
        return self.clean_internet_df

    def latest_price_by_country(self):
        """get the latest price regulation row for each country"""
        if self.clean_price_df is None:
            self.clean_price_data()  # clean first

        latest = (
            self.clean_price_df
            .sort_values("dataYear")
            .groupby("entityIso", as_index=False)
            .tail(1)
            .reset_index(drop=True)
        )  # keep latest price row

        return latest

    def latest_internet_by_country(self):
        """get the latest internet usage row for each country"""
        if self.clean_internet_df is None:
            self.clean_internet_data()  # clean first

        latest = (
            self.clean_internet_df
            .sort_values("internet_year")
            .groupby("entityIso", as_index=False)
            .tail(1)
            .reset_index(drop=True)
        )  # keep latest internet row

        return latest

    def merge_with_internet_usage(self):
        """merge price regulation data with internet usage data"""
        price_latest = self.latest_price_by_country()  # get price regulation data
        internet_latest = self.latest_internet_by_country()  # get internet usage data

        merged = pd.merge(
            price_latest,
            internet_latest[["entityIso", "internet_usage", "internet_year"]],
            on="entityIso",
            how="inner"
        )  # merge by country code

        self.merged_df = merged.reset_index(drop=True)  # save merged data
        return self.merged_df

    def filter_by_country(self, iso):
        """filter the price regulation data by country code"""
        if self.clean_price_df is None:
            self.clean_price_data()  # clean first

        result = self.clean_price_df[self.clean_price_df["entityIso"] == iso.upper()].copy()  # filter country

        if result.empty:
            raise ValueError(f"No price regulation data found for {iso}")

        return result

    def recursive_country_count(self, countries):
        """count countries using recursion"""
        if len(countries) == 0:
            return 0  # stop recursion
        return 1 + self.recursive_country_count(countries[1:])  # count one country
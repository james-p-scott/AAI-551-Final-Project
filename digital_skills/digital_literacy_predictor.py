"""
digital_literacy_predictor.py

Defines the DigitalLiteracyPredictor class, which uses a small PyTorch MLP
to extrapolate future ICT skill rates for a given country from its historical
total-population data.

One model is trained per (country, skill_category) pair. Years are normalised
to zero mean / unit variance before training so the optimiser converges quickly
on the small datasets typical of ITU reports (5-20 observations per country).
"""

import datetime
import os
import sys

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
import torch
import torch.nn as nn
from torch.optim import Adam

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from digital_skills.digital_skills_analyzer import DigitalSkillsAnalyzer

class _TrendMLP(nn.Module):
    """
    Minimal two-layer MLP that maps a normalised year scalar to a predicted
    ICT skill rate.

    Architecture: Linear(1→32) → ReLU → Linear(32→16) → ReLU → Linear(16→1)

    Kept intentionally small: ITU datasets typically have fewer than 20
    observations per country per category, so a larger network would overfit.
    """

    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(1, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class DigitalLiteracyPredictor:
    """
    Trains one _TrendMLP per (country, skill_category) pair on historical
    total-population ICT skill data and uses the trained model to predict
    future proficiency rates.

    Composes a DigitalSkillsAnalyzer to access the underlying data.
    """

    def __init__(self, analyzer: DigitalSkillsAnalyzer):
        """
        Construct a DigitalLiteracyPredictor backed by an existing analyzer.
        Parameters:
            analyzer (DigitalSkillsAnalyzer): Loaded analyzer that provides
                historical ICT skill data.
        Raises:
            TypeError: If analyzer is not a DigitalSkillsAnalyzer.
        """
        if not isinstance(analyzer, DigitalSkillsAnalyzer):
            raise TypeError(
                f"analyzer must be a DigitalSkillsAnalyzer, "
                f"got {type(analyzer).__name__}."
            )
        self.analyzer: DigitalSkillsAnalyzer = analyzer

        # Trained model cache: (country_iso, skill_category) → dict with
        # keys "model", "year_mean", "year_std"
        self._models: dict = {}

    def __str__(self) -> str:
        """
        Return a summary of the predictor and its trained models.
        Returns:
            str: Human-readable summary.
        """
        lines = [
            f"DigitalLiteracyPredictor — "
            f"{len(self._models)} trained model(s):"
        ]
        for (iso, cat) in self._models:
            lines.append(f"  [{iso}]  {cat}")
        return "\n".join(lines)

    def _get_history(self, country_iso: str, skill_category: str) -> pd.DataFrame:
        """
        Retrieve the historical total-population time-series for a country and
        skill category, sorted by year and deduplicated to one mean value per year.

        Parameters:
            country_iso (str): country code.
            skill_category (str): One of the managed skill categories.
        Returns:
            DataFrame: Columns dataYear (int) and mean_value (float).
        Raises:
            ValueError: If fewer than two data points are available.
        """
        ds = self.analyzer._get_dataset(skill_category)
        iso_upper = country_iso.upper()

        if iso_upper not in ds.available_countries:
            raise ValueError(
                f"Country '{country_iso}' not found in "
                f"the '{skill_category}' dataset."
            )

        country_df = ds.filter_by_country(iso_upper)
        totals = country_df[country_df["seriesParent"].isna()].copy()
        totals["dataValue"] = pd.to_numeric(totals["dataValue"], errors="coerce")

        history = (
            totals
            .groupby("dataYear", as_index=False)["dataValue"]
            .mean()
            .rename(columns={"dataValue": "mean_value"})
            .sort_values("dataYear")
            .reset_index(drop=True)
        )
        history["dataYear"] = history["dataYear"].astype(int)

        if len(history) < 2:
            raise ValueError(
                f"Not enough historical data to train a model for "
                f"'{country_iso}' / '{skill_category}' "
                f"(need ≥ 2 years, found {len(history)})."
            )
        return history

    @staticmethod
    def _normalise(years: torch.Tensor, mean: float, std: float) -> torch.Tensor:
        """Standardise year values using pre-computed mean and std."""
        return (years - mean) / std

    def fit(
        self,
        country_iso: str,
        skill_category: str,
        epochs: int = 2000,
        learning_rate: float = 1e-3,
    ) -> dict:
        """
        Train a _TrendMLP on the historical ICT skill data for one country and
        skill category, caching the trained model for later prediction.

        Parameters:
            country_iso (str): country code.
            skill_category (str): One of the managed skill categories.
            epochs (int): Number of gradient-descent steps. Defaults to 2000.
            learning_rate (float): Adam optimiser learning rate. Defaults to 1e-3.
        Returns:
            dict: Keys country_iso, skill_category, epochs, and final_loss.
        Raises:
            ValueError: If insufficient historical data is available.
        """
        history = self._get_history(country_iso, skill_category)

        years = torch.tensor(
            history["dataYear"].values, dtype=torch.float32
        ).unsqueeze(1)
        values = torch.tensor(
            history["mean_value"].values, dtype=torch.float32
        ).unsqueeze(1)

        # Normalise years so the optimiser converges regardless of century offset
        year_mean = float(years.mean())
        year_std = float(years.std()) if float(years.std()) > 0 else 1.0

        years_norm = self._normalise(years, year_mean, year_std)

        model = _TrendMLP()
        optimiser = Adam(model.parameters(), lr=learning_rate)
        loss_fn = nn.MSELoss()

        model.train()
        for _ in range(epochs):
            optimiser.zero_grad()
            pred = model(years_norm)
            loss = loss_fn(pred, values)
            loss.backward()
            optimiser.step()

        final_loss = float(loss.item())
        model.eval()

        key = (country_iso.upper(), skill_category)
        self._models[key] = {
            "model":     model,
            "year_mean": year_mean,
            "year_std":  year_std,
        }

        return {
            "country_iso":    country_iso.upper(),
            "skill_category": skill_category,
            "epochs":         epochs,
            "final_loss":     round(final_loss, 4),
        }

    def predict(
        self,
        country_iso: str,
        skill_category: str,
        years: list,
    ) -> pd.DataFrame:
        """
        Return predicted ICT skill rates for a list of future (or any) years.
        The model is trained automatically if it has not been fitted yet.

        Parameters:
            country_iso (str): country code.
            skill_category (str): One of the managed skill categories.
            years (list): Integer calendar years to predict (e.g. [2025, 2026]).
        Returns:
            DataFrame: Columns year, predicted_value, and skill_category.
                predicted_value is clamped to [0, 100].
        Raises:
            ValueError: If years is empty, or if training data is unavailable.
        """
        if not years:
            raise ValueError("years list must not be empty.")

        key = (country_iso.upper(), skill_category)
        if key not in self._models:
            self.fit(country_iso, skill_category)

        entry = self._models[key]
        model: _TrendMLP = entry["model"]
        year_mean: float = entry["year_mean"]
        year_std: float = entry["year_std"]

        year_tensor = torch.tensor(
            [[float(y)] for y in years], dtype=torch.float32
        )
        year_norm = self._normalise(year_tensor, year_mean, year_std)

        model.eval()
        with torch.no_grad():
            raw = model(year_norm).squeeze(1)

        # Clamp predictions to a valid percentage range
        clamped = torch.clamp(raw, 0.0, 100.0).tolist()

        return pd.DataFrame({
            "year":             [int(y) for y in years],
            "predicted_value":  [round(v, 2) for v in clamped],
            "skill_category":   skill_category,
        })

    def predict_all_categories(
        self,
        country_iso: str,
        years_ahead: int = 5,
    ) -> pd.DataFrame:
        """
        Train one model per loaded skill category and return predictions for
        each of the next years_ahead years beyond the most recent data year.

        Parameters:
            country_iso (str): country code.
            years_ahead (int): Number of future years to predict. Defaults to 5.
        Returns:
            DataFrame: Columns year, predicted_value, and skill_category for
                every category that has enough data for the given country.
        Raises:
            ValueError: If no categories have sufficient data for the country,
                or if years_ahead is less than 1.
        """
        if years_ahead < 1:
            raise ValueError("years_ahead must be a positive integer.")

        frames = []
        for ds in self.analyzer.datasets:
            category = ds.skill_category
            try:
                history = self._get_history(country_iso, category)
            except ValueError:
                continue

            last_year = int(history["dataYear"].max())
            current_year = datetime.date.today().year
            if last_year < current_year:
                # Predict every gap year so the model has continuity
                all_years = list(range(last_year + 1, current_year + years_ahead))
                predictions = self.predict(country_iso, category, all_years)
            else:
                future_years = list(range(last_year + 1, last_year + years_ahead + 1))
                predictions = self.predict(country_iso, category, future_years)
            frames.append(predictions)

        if not frames:
            raise ValueError(
                f"No categories had sufficient historical data for '{country_iso}'."
            )

        return pd.concat(frames, ignore_index=True).sort_values(
            ["skill_category", "year"]
        ).reset_index(drop=True)

    def plot_predicted_growth(
        self,
        country_iso: str,
        years_ahead: int = 5,
    ) -> plt.Figure:
        """
        Plot the historical ICT skill rates and the predicted future values for
        every loaded skill category for a given country.

        Historical data is shown as solid lines with markers; predicted values
        are shown as dashed lines so the two regions are visually distinct.

        Parameters:
            country_iso (str): country code.
            years_ahead (int): Number of future years to forecast and plot.
                Defaults to 5.
        Returns:
            Figure: matplotlib Figure object.
        Raises:
            ValueError: If no categories have sufficient data for the country.
        """
        forecast_df = self.predict_all_categories(country_iso, years_ahead=years_ahead)
        categories = forecast_df["skill_category"].unique().tolist()

        fig, ax = plt.subplots(figsize=(12, 6))
        color_cycle = plt.rcParams["axes.prop_cycle"].by_key()["color"]

        for i, category in enumerate(sorted(categories)):
            color = color_cycle[i % len(color_cycle)]

            # Historical series
            history = self._get_history(country_iso, category)
            ax.plot(
                history["dataYear"],
                history["mean_value"],
                color=color,
                linewidth=2,
                marker="o",
                markersize=4,
                label=category,
            )

            # Predicted series — connect from last historical point
            cat_forecast = forecast_df[forecast_df["skill_category"] == category]
            last_hist_year = int(history["dataYear"].iloc[-1])
            last_hist_val = float(history["mean_value"].iloc[-1])

            pred_years = [last_hist_year] + cat_forecast["year"].tolist()
            pred_vals = [last_hist_val] + cat_forecast["predicted_value"].tolist()

            ax.plot(
                pred_years,
                pred_vals,
                color=color,
                linewidth=2,
                linestyle="--",
            )

        ax.set_title(
            f"ICT Skill Rate Forecast — {country_iso.upper()}",
            fontsize=14,
            fontweight="bold",
        )
        ax.set_xlabel("Year")
        ax.set_ylabel("Skill Proficiency (%)")
        ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=100))
        ax.legend(title="Skill Category", bbox_to_anchor=(1.02, 1), loc="upper left")
        ax.grid(axis="y", linestyle="--", alpha=0.4)

        current_year = datetime.date.today().year
        ax.axvline(x=current_year, color="gray", linestyle=":", linewidth=1.5,
                   label="Today")

        fig.tight_layout()
        return fig


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from digital_skills.ict_skills_dataset import ICTSkillsDataset
    from digital_skills.digital_skills_analyzer import DigitalSkillsAnalyzer
    from digital_skills.digital_literacy_predictor import DigitalLiteracyPredictor

    print("DigitalLiteracyPredictor smoke test\n")

    ds_safety = ICTSkillsDataset("safety")
    ds_problem = ICTSkillsDataset("problem-solving")
    analyzer = DigitalSkillsAnalyzer([ds_safety, ds_problem])
    predictor = DigitalLiteracyPredictor(analyzer)

    print("Training model for KOR / safety...")
    result = predictor.fit("KOR", "safety")
    print(f"Final loss: {result['final_loss']}")

    print("\nPredictions for 2025-2029 (safety, KOR):")
    print(predictor.predict("KOR", "safety", [2025, 2026, 2027, 2028, 2029]))

    print("\nAll-category predictions for KOR (5 years ahead):")
    print(predictor.predict_all_categories("KOR", years_ahead=5))

    print("\nPredictor summary:")
    print(predictor)

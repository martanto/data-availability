from __future__ import annotations

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

from data_availability.data import load_data
from data_availability.plot import plot_availability as _plot_availability


class PlotAvailability:
    def __init__(self, filepath: str | Path) -> None:
        self._filepath = Path(filepath)
        self._df: pd.DataFrame | None = None
        self._date_column: str = "date"
        self._completeness_column: str = "completeness"

    def load_data(
        self,
        date_column: str = "date",
        completeness_column: str = "completeness",
    ) -> PlotAvailability:
        self._date_column = date_column
        self._completeness_column = completeness_column
        self._df = load_data(self._filepath, date_column, completeness_column)
        return self

    def plot_availability(
        self,
        title: str = "Data Availability",
        hspace: float = 0.2,
        cbar_bottom: float = 0.012,
        cbar_height: float = 0.005,
        tile_gap: float = 0.9,
        figsize_per_year: float = 2.2,
        missing_color: str = "#e0e0e0",
    ) -> plt.Figure:
        if self._df is None:
            raise RuntimeError("Call .load_data() before .plot_availability().")
        return _plot_availability(
            self._filepath,
            title=title,
            date_column=self._date_column,
            completeness_column=self._completeness_column,
            hspace=hspace,
            cbar_bottom=cbar_bottom,
            cbar_height=cbar_height,
            tile_gap=tile_gap,
            figsize_per_year=figsize_per_year,
            missing_color=missing_color,
        )

from __future__ import annotations

from typing import Literal
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

from data_availability.data import load_data
from data_availability.plot import plot_from_df as _plot_from_df


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
        years: str | list[str] | None = None,
    ) -> PlotAvailability:
        self._date_column = date_column
        self._completeness_column = completeness_column
        self._df = load_data(self._filepath, date_column, completeness_column)
        if years is not None:
            selected = [str(y) for y in ([years] if isinstance(years, str) else years)]
            mask = self._df[date_column].dt.year.astype(str).isin(selected)
            self._df = self._df[mask].reset_index(drop=True)
            if isinstance(self._df, pd.DataFrame) and self._df.empty:
                raise ValueError(
                    f"No data found for the specified year(s): {selected}."
                )
        return self

    def plot_availability(
        self,
        title: str = "Data Availability",
        hspace: float = 0.2,
        cbar_bottom: int = 20,
        cbar_height: int = 10,
        tile_gap: float = 0.9,
        figsize_per_year: float = 2.2,
        missing_color: str = "#e0e0e0",
        tile_shape: Literal["square", "squircle"] = "square",
        title_pad: int = 40,
    ) -> plt.Figure:
        """Build a GitHub-style calendar heatmap of data completeness over time.

        Args:
            title: Figure super-title rendered above all subplots.
            hspace: Vertical spacing between year subplots.
            cbar_bottom: Gap in pixels between the bottom edge of the last subplot
                and the top of the colorbar.
            cbar_height: Height of the colorbar in pixels.
            tile_gap: Side length of each day tile (values < 1 add whitespace
                between tiles).
            figsize_per_year: Figure height in inches allocated per year subplot.
            missing_color: Color used for calendar days absent from the input data.
            tile_shape: Shape of each day tile. ``"square"`` draws plain rectangles;
                ``"squircle"`` draws rectangles with rounded corners.
            title_pad: Gap in pixels between the top of the last subplot and the
                figure super-title.

        Returns:
            A :class:`matplotlib.figure.Figure` containing the heatmap.

        Raises:
            RuntimeError: If :meth:`load_data` has not been called first.
        """
        if self._df is None:
            raise RuntimeError("Call .load_data() before .plot_availability().")
        return _plot_from_df(
            self._df,
            title=title,
            date_column=self._date_column,
            completeness_column=self._completeness_column,
            hspace=hspace,
            cbar_bottom=cbar_bottom,
            cbar_height=cbar_height,
            tile_gap=tile_gap,
            figsize_per_year=figsize_per_year,
            missing_color=missing_color,
            tile_shape=tile_shape,
            title_pad=title_pad,
        )

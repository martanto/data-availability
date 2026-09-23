from __future__ import annotations

from typing import Literal
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

from data_availability.data import load_data
from data_availability.plot import plot_from_df as _plot_from_df


class PlotAvailability:
    """Fluent builder for GitHub-style calendar heatmaps from file-based data.

    Chain :meth:`select` then :meth:`plot` to load data and produce a figure.

    Args:
        filepath: Path to an ``.xlsx``, ``.xls``, or ``.csv`` file.

    Example:
        >>> fig = (
        ...     PlotAvailability("data.xlsx")
        ...     .select(years="2023")
        ...     .plot(title="Sensor Uptime", tile_shape="squircle")
        ... )
        >>> fig.savefig("availability.png", dpi=150, bbox_inches="tight")
    """

    def __init__(self, filepath: str | Path) -> None:
        self._filepath = Path(filepath)
        self._df: pd.DataFrame | None = None
        self._date_column: str = "date"
        self._completeness_column: str = "completeness"

    def select(
        self,
        date_column: str = "date",
        completeness_column: str = "completeness",
        years: str | list[str] | None = None,
    ) -> PlotAvailability:
        """Load and optionally filter data from the file supplied at construction.

        Args:
            date_column: Name of the date column in the source file.
            completeness_column: Name of the completeness column (0–100) in the
                source file.
            years: One or more years to keep, e.g. ``"2023"`` or
                ``["2022", "2023"]``. All years are kept when omitted.

        Returns:
            ``self`` — enables method chaining.

        Raises:
            KeyError: If the required columns are absent from the file.
            ValueError: If ``years`` is specified but no matching rows exist.
        """
        self._date_column = date_column
        self._completeness_column = completeness_column
        self._df = load_data(self._filepath, date_column, completeness_column)

        if years is not None:
            selected = [str(y) for y in ([years] if isinstance(years, str) else years)]
            mask = self._df[date_column].dt.year.astype(str).isin(selected)
            self._df = self._df[mask].reset_index(drop=True)

        if isinstance(self._df, pd.DataFrame) and self._df.empty:
            raise ValueError("No data found.")

        return self

    def plot(
        self,
        title: str = "Data Availability",
        kind: Literal["calendar", "bar"] = "calendar",
        hspace: float | None = None,
        cbar_bottom: int = 20,
        cbar_height: int = 10,
        tile_gap: float = 0.9,
        figsize_per_year: float | None = None,
        fig_width: float = 20.0,
        missing_color: str = "#e0e0e0",
        tile_shape: Literal["square", "squircle"] = "square",
        title_pad: int = 40,
        bar_gap: float = 0.8,
    ) -> plt.Figure:
        """Build a figure of data completeness over time.

        Args:
            title: Figure super-title rendered above all subplots.
            kind: ``"calendar"`` for a GitHub-style heatmap; ``"bar"`` for a
                status-page style daily bar strip.
            hspace: Vertical spacing between year subplots. Defaults to
                ``0.2`` for calendar and ``1.4`` for bar.
            cbar_bottom: Gap in pixels between the bottom edge of the last
                subplot (for bar, its month labels) and the colorbar.
            cbar_height: Height of the colorbar in pixels.
            tile_gap: Calendar only. Side length of each day tile (values < 1
                add whitespace between tiles).
            figsize_per_year: Figure height in inches allocated per year
                subplot. Defaults to ``2.2`` for calendar and ``1.2`` for bar.
            fig_width: Figure width in inches. Defaults to ``20``.
            missing_color: Color used for calendar days absent from the input data.
            tile_shape: Calendar only. ``"square"`` draws plain rectangles;
                ``"squircle"`` draws rectangles with rounded corners.
            title_pad: Gap in pixels between the top of the first subplot and
                the figure super-title.
            bar_gap: Bar only. Width of each day bar (values < 1 add
                whitespace between bars).

        Returns:
            A :class:`matplotlib.figure.Figure`.

        Raises:
            RuntimeError: If :meth:`select` has not been called first.
            ValueError: If ``kind`` is not ``"calendar"`` or ``"bar"``.
        """
        if self._df is None:
            raise RuntimeError("Call .select() before .plot().")

        return _plot_from_df(
            self._df,
            title=title,
            date_column=self._date_column,
            completeness_column=self._completeness_column,
            kind=kind,
            hspace=hspace,
            cbar_bottom=cbar_bottom,
            cbar_height=cbar_height,
            tile_gap=tile_gap,
            figsize_per_year=figsize_per_year,
            fig_width=fig_width,
            missing_color=missing_color,
            tile_shape=tile_shape,
            title_pad=title_pad,
            bar_gap=bar_gap,
        )

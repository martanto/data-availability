from typing import Literal
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from data_availability.data import load_data


def _build_figure(
    df: pd.DataFrame,
    title: str,
    date_column: str,
    completeness_column: str,
    hspace: float,
    cbar_bottom: float,
    cbar_height: int,
    tile_gap: float,
    figsize_per_year: float,
    missing_color: str,
    tile_shape: Literal["square", "squircle"],
) -> plt.Figure:
    years = sorted(df[date_column].dt.year.unique())
    n_years = len(years)

    fig, axes = plt.subplots(n_years, 1, figsize=(20, n_years * figsize_per_year))
    if n_years == 1:
        axes = [axes]

    cmap = mcolors.LinearSegmentedColormap.from_list(
        "rg", ["#d73027", "#fee08b", "#1a9850"]
    )
    norm = mcolors.Normalize(vmin=0, vmax=100)

    day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    for ax, year in zip(axes, years, strict=True):
        year_dates = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
        year_df = df[df[date_column].dt.year == year].set_index(date_column)[
            completeness_column
        ]

        # Build a 7-row (weekday) x 53-col (week) grid
        grid = np.full((7, 53), np.nan)
        has_data = np.zeros((7, 53), dtype=bool)

        for date in year_dates:
            # GitHub-style: week col starts from the week of Jan 1
            day_of_year = date.day_of_year - 1  # 0-indexed
            # week column: offset by weekday of Jan 1
            jan1_weekday = pd.Timestamp(f"{year}-01-01").weekday()  # Mon=0
            col = (day_of_year + jan1_weekday) // 7
            row = date.weekday()  # Mon=0, Sun=6
            has_data[row, col] = True
            if date in year_df.index:
                grid[row, col] = year_df[date]
            else:
                grid[row, col] = np.nan  # missing = will render grey

        # Draw tiles
        rounding = tile_gap * 0.3
        for col in range(53):
            for row in range(7):
                if not has_data[row, col]:
                    continue
                val = grid[row, col]
                color = missing_color if np.isnan(val) else cmap(norm(val))
                if tile_shape == "squircle":
                    patch = mpatches.FancyBboxPatch(
                        (col, 6 - row),
                        tile_gap,
                        tile_gap,
                        boxstyle=f"round,pad=0,rounding_size={rounding}",
                        facecolor=color,
                        edgecolor="white",
                        linewidth=0.5,
                    )
                else:
                    patch = mpatches.Rectangle(
                        (col, 6 - row),
                        tile_gap,
                        tile_gap,
                        facecolor=color,
                        edgecolor="white",
                        linewidth=0.5,
                    )
                ax.add_patch(patch)

        # Month label positions
        month_starts = {}
        for date in year_dates:
            if date.day == 1:
                jan1_weekday = pd.Timestamp(f"{year}-01-01").weekday()
                day_of_year = date.day_of_year - 1
                col = (day_of_year + jan1_weekday) // 7
                month_starts[date.strftime("%b")] = col

        for month, col in month_starts.items():
            ax.text(
                col + 0.4,
                7.2,
                month,
                ha="center",
                va="bottom",
                fontsize=7,
                color="#555",
            )

        ax.set_xlim(0, 53)
        ax.set_ylim(-0.2, 7.8)
        ax.set_aspect("equal")
        ax.set_yticks([6 - r + tile_gap / 2 for r in range(7)])
        ax.set_yticklabels(day_labels, fontsize=7)
        ax.set_xticks([])
        ax.set_ylabel(str(year), fontsize=9, rotation=0, labelpad=30, va="center")
        ax.set_frame_on(False)
        ax.tick_params(left=False)

    fig.subplots_adjust(hspace=hspace)

    # Get the bounding box of the last subplot to anchor the colorbar tightly below it
    fig.canvas.draw()
    last_ax = axes[-1]
    first_ax = axes[0]
    pos_last = last_ax.get_position()
    pos_first = first_ax.get_position()

    cbar_width = (pos_last.x1 - pos_last.x0) * 0.8
    cbar_left = pos_last.x0 + (pos_last.x1 - pos_last.x0) * 0.1
    fig_height_px = fig.get_size_inches()[1] * fig.dpi
    cbar_height_fraction = cbar_height / fig_height_px
    cbar_ax = fig.add_axes(
        [cbar_left, pos_last.y0 - cbar_bottom, cbar_width, cbar_height_fraction]
    )

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, cax=cbar_ax, orientation="horizontal")
    cbar.set_label("Completeness (%)", fontsize=9)
    cbar.ax.tick_params(labelsize=8)

    fig.suptitle(title, fontsize=13, fontweight="bold", y=pos_first.y1 + 0.02)

    return fig


def plot_from_file(
    filepath: str | Path,
    title: str = "Data Availability",
    date_column: str = "date",
    completeness_column: str = "completeness",
    hspace: float = 0.2,
    cbar_bottom: float = 0.012,
    cbar_height: int = 10,
    tile_gap: float = 0.9,
    figsize_per_year: float = 2.2,
    missing_color: str = "#e0e0e0",
    tile_shape: Literal["square", "squircle"] = "square",
) -> plt.Figure:
    """Build a GitHub-style calendar heatmap of data completeness from a file.

    Loads data from an Excel or CSV file, then creates one subplot per calendar
    year found in the data. Each day is rendered as a colored tile on a
    Mon–Sun × week grid, color-coded on a red-yellow-green gradient according
    to completeness. Days present in the calendar but absent from the dataset
    are rendered in ``missing_color``. A horizontal colorbar is anchored below
    the last subplot.

    Args:
        filepath: Path to an ``.xlsx``, ``.xls``, or ``.csv`` file accepted by
            :func:`~data_availability.data.load_data`.
        title: Figure super-title rendered above all subplots.
        hspace: Vertical spacing between year subplots, passed to
            ``Figure.subplots_adjust``.
        cbar_bottom: Gap (in figure-fraction units) between the bottom edge of
            the last subplot and the top of the colorbar.
        cbar_height: Height of the colorbar in pixels.
        tile_gap: Side length of each day tile (values < 1 add whitespace
            between tiles).
        figsize_per_year: Figure height in inches allocated per year subplot.
            Total height is ``n_years * figsize_per_year``.
        missing_color: Hex or named color used for calendar days that have no
            corresponding row in the input data.
        tile_shape: ``"square"`` draws plain rectangles; ``"squircle"`` draws
            rectangles with rounded corners.

    Returns:
        A :class:`matplotlib.figure.Figure` containing the heatmap. The figure
        is not saved or displayed; call ``fig.savefig()`` or ``plt.show()`` as
        needed.
    """
    df = load_data(
        filepath, date_column=date_column, completeness_column=completeness_column
    )
    return _build_figure(
        df,
        title=title,
        date_column=date_column,
        completeness_column=completeness_column,
        hspace=hspace,
        cbar_bottom=cbar_bottom,
        cbar_height=cbar_height,
        tile_gap=tile_gap,
        figsize_per_year=figsize_per_year,
        missing_color=missing_color,
        tile_shape=tile_shape,
    )


def plot_from_df(
    df: pd.DataFrame,
    title: str = "Data Availability",
    date_column: str = "date",
    completeness_column: str = "completeness",
    hspace: float = 0.2,
    cbar_bottom: float = 0.012,
    cbar_height: int = 10,
    tile_gap: float = 0.9,
    figsize_per_year: float = 2.2,
    missing_color: str = "#e0e0e0",
    tile_shape: Literal["square", "squircle"] = "square",
) -> plt.Figure:
    """Build a GitHub-style calendar heatmap from an in-memory DataFrame.

    Identical to :func:`plot_from_file` but accepts a pre-loaded
    :class:`~pandas.DataFrame` instead of a file path. Useful when the data
    has already been loaded and optionally filtered before plotting.

    Args:
        df: DataFrame with a datetime ``date_column`` and a numeric
            ``completeness_column`` (0–100).
        title: Figure super-title rendered above all subplots.
        hspace: Vertical spacing between year subplots.
        cbar_bottom: Gap (in figure-fraction units) between the bottom edge of
            the last subplot and the top of the colorbar.
        cbar_height: Height of the colorbar in pixels.
        tile_gap: Side length of each day tile (values < 1 add whitespace
            between tiles).
        figsize_per_year: Figure height in inches allocated per year subplot.
        missing_color: Hex or named color used for calendar days absent from
            the input data.
        tile_shape: ``"square"`` draws plain rectangles; ``"squircle"`` draws
            rectangles with rounded corners.

    Returns:
        A :class:`matplotlib.figure.Figure` containing the heatmap.
    """
    return _build_figure(
        df,
        title=title,
        date_column=date_column,
        completeness_column=completeness_column,
        hspace=hspace,
        cbar_bottom=cbar_bottom,
        cbar_height=cbar_height,
        tile_gap=tile_gap,
        figsize_per_year=figsize_per_year,
        missing_color=missing_color,
        tile_shape=tile_shape,
    )

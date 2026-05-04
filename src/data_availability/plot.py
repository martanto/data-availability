from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt

from data_availability.data import load_data


def plot_availability(
    filepath: str | Path,
    title: str = "Data Availability",
    hspace: float = 0.2,
    cbar_bottom: float = 0.012,
    cbar_height: float = 0.005,
    tile_gap: float = 0.9,
    figsize_per_year: float = 2.2,
    missing_color: str = "#e0e0e0",
) -> plt.Figure:
    df = load_data(filepath)

    years = sorted(df["date"].dt.year.unique())
    n_years = len(years)

    fig, axes = plt.subplots(n_years, 1, figsize=(20, n_years * figsize_per_year))
    if n_years == 1:
        axes = [axes]

    cmap = mcolors.LinearSegmentedColormap.from_list("rg", ["#d73027", "#fee08b", "#1a9850"])
    norm = mcolors.Normalize(vmin=0, vmax=100)

    day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    for ax, year in zip(axes, years, strict=True):
        year_dates = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
        year_df = df[df["date"].dt.year == year].set_index("date")["completeness"]

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
        for col in range(53):
            for row in range(7):
                if not has_data[row, col]:
                    continue
                val = grid[row, col]
                if np.isnan(val):
                    color = missing_color
                else:
                    color = cmap(norm(val))
                rect = plt.Rectangle(
                    (col, 6 - row), tile_gap, tile_gap,
                    facecolor=color,
                    edgecolor="white",
                    linewidth=0.5,
                )
                ax.add_patch(rect)

        # Month label positions
        month_starts = {}
        for date in year_dates:
            if date.day == 1:
                jan1_weekday = pd.Timestamp(f"{year}-01-01").weekday()
                day_of_year = date.day_of_year - 1
                col = (day_of_year + jan1_weekday) // 7
                month_starts[date.strftime("%b")] = col

        for month, col in month_starts.items():
            ax.text(col + 0.4, 7.2, month, ha="center", va="bottom", fontsize=7, color="#555")

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
    cbar_ax = fig.add_axes([cbar_left, pos_last.y0 - cbar_bottom, cbar_width, cbar_height])

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, cax=cbar_ax, orientation="horizontal")
    cbar.set_label("Completeness (%)", fontsize=9)
    cbar.ax.tick_params(labelsize=8)

    fig.suptitle(title, fontsize=13, fontweight="bold", y=pos_first.y1 + 0.02)

    return fig
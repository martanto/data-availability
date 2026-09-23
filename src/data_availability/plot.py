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
    cbar_bottom: int,
    cbar_height: int,
    tile_gap: float,
    figsize_per_year: float,
    missing_color: str,
    tile_shape: Literal["square", "squircle"],
    title_pad: int,
) -> plt.Figure:
    """Render a GitHub-style calendar heatmap from a pre-validated DataFrame.

    Internal helper called by :func:`plot_from_file` and :func:`plot_from_df`.
    Creates one subplot per calendar year in ``df``, draws day tiles on a
    Mon–Sun × week grid, attaches a horizontal colorbar below the last subplot,
    and places a super-title above the first.

    Args:
        df: DataFrame with a datetime ``date_column`` and a numeric
            ``completeness_column`` (0–100), sorted ascending by date.
        title: Figure super-title rendered above all subplots.
        date_column: Name of the datetime column in ``df``.
        completeness_column: Name of the numeric completeness column (0–100).
        hspace: Vertical spacing between year subplots, passed to
            ``Figure.subplots_adjust``.
        cbar_bottom: Gap in pixels between the bottom edge of the last subplot
            and the top of the colorbar.
        cbar_height: Height of the colorbar in pixels.
        tile_gap: Side length of each day tile; values less than 1 add
            whitespace between tiles.
        figsize_per_year: Figure height in inches allocated per year subplot.
            Total figure height is ``n_years * figsize_per_year``.
        missing_color: Hex or named color for calendar days absent from
            ``df``.
        tile_shape: ``"square"`` draws plain rectangles; ``"squircle"`` draws
            rectangles with rounded corners.
        title_pad: Gap in pixels between the top of the first subplot and the
            figure super-title.

    Returns:
        A :class:`matplotlib.figure.Figure` containing the heatmap.
    """
    years: list[str] = sorted(df[date_column].dt.year.unique())
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
    cbar_bottom_fraction = cbar_bottom / fig_height_px
    cbar_ax = fig.add_axes(
        [
            cbar_left,
            pos_last.y0 - cbar_bottom_fraction,
            cbar_width,
            cbar_height_fraction,
        ]
    )

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, cax=cbar_ax, orientation="horizontal")
    cbar.set_label("Completeness (%)", fontsize=9)
    cbar.ax.tick_params(labelsize=8)

    title_pad_fraction = title_pad / fig_height_px
    fig.suptitle(
        title, fontsize=13, fontweight="bold", y=pos_first.y1 + title_pad_fraction
    )

    return fig


def _build_bar_figure(
    df: pd.DataFrame,
    title: str,
    date_column: str,
    completeness_column: str,
    hspace: float,
    figsize_per_year: float,
    missing_color: str,
    healthy_threshold: float,
    status_colors: tuple[str, str, str],
    status_labels: tuple[str, str, str],
    bar_gap: float,
    title_pad: int,
) -> plt.Figure:
    """Render a status-page style daily bar strip from a pre-validated DataFrame.

    Internal helper called by :func:`plot_from_df` when ``kind="bar"``.
    Creates one subplot per calendar year in ``df``, each a horizontal strip of
    one bar per day. Bars are colored by status: healthy
    (``>= healthy_threshold``), issue (between 0 and the threshold) or
    downtime (``== 0``). Days absent from ``df`` are drawn in
    ``missing_color``.

    Args:
        df: DataFrame with a datetime ``date_column`` and a numeric
            ``completeness_column`` (0–100), sorted ascending by date.
        title: Figure super-title rendered above all subplots.
        date_column: Name of the datetime column in ``df``.
        completeness_column: Name of the numeric completeness column (0–100).
        hspace: Vertical spacing between year subplots, passed to
            ``Figure.subplots_adjust``.
        figsize_per_year: Figure height in inches allocated per year subplot.
        missing_color: Hex or named color for calendar days absent from
            ``df``.
        healthy_threshold: Minimum completeness (0–100) for a day to count as
            healthy.
        status_colors: Colors for the healthy, issue and downtime statuses.
        status_labels: Legend labels for the healthy, issue and downtime
            statuses.
        bar_gap: Width of each day bar; values less than 1 add whitespace
            between bars.
        title_pad: Gap in pixels between the top of the first subplot and the
            figure super-title.

    Returns:
        A :class:`matplotlib.figure.Figure` containing the bar strips.
    """
    years: list[int] = sorted(df[date_column].dt.year.unique())
    n_years = len(years)

    fig, axes = plt.subplots(n_years, 1, figsize=(20, n_years * figsize_per_year))
    if n_years == 1:
        axes = [axes]

    healthy_color, issue_color, downtime_color = status_colors

    for ax, year in zip(axes, years, strict=True):
        year_dates = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
        year_df = df[df[date_column].dt.year == year]
        values = (
            year_df.groupby(year_df[date_column].dt.normalize())[completeness_column]
            .mean()
            .reindex(year_dates)
            .to_numpy()
        )

        colors = np.select(
            [
                np.isnan(values),
                values <= 0,
                values >= healthy_threshold,
            ],
            [missing_color, downtime_color, healthy_color],
            default=issue_color,
        )

        ax.bar(
            np.arange(len(year_dates)),
            height=1,
            width=bar_gap,
            color=colors,
            align="edge",
        )

        month_starts = [date for date in year_dates if date.day == 1]
        ax.set_xticks([date.day_of_year - 1 for date in month_starts])
        ax.set_xticklabels(
            [date.strftime("%b") for date in month_starts], fontsize=8, color="#555"
        )
        ax.tick_params(bottom=False, left=False)
        ax.set_xlim(0, len(year_dates))
        ax.set_ylim(0, 1)
        ax.set_yticks([])
        ax.set_frame_on(False)
        ax.set_title(str(year), loc="left", fontsize=10, color="#333")

    handles = [
        mpatches.Patch(color=color, label=label)
        for color, label in zip(status_colors, status_labels, strict=True)
    ]
    handles.append(mpatches.Patch(color=missing_color, label="Missing"))
    axes[0].legend(
        handles=handles,
        loc="lower right",
        bbox_to_anchor=(1, 1),
        ncol=len(handles),
        frameon=False,
        fontsize=8,
        handlelength=1,
        handleheight=1,
    )

    fig.subplots_adjust(hspace=hspace)

    fig.canvas.draw()
    pos_first = axes[0].get_position()
    fig_height_px = fig.get_size_inches()[1] * fig.dpi
    title_pad_fraction = title_pad / fig_height_px
    fig.suptitle(
        title, fontsize=13, fontweight="bold", y=pos_first.y1 + title_pad_fraction
    )

    return fig


_DEFAULT_FIGSIZE_PER_YEAR: dict[str, float] = {"calendar": 2.2, "bar": 1.2}
_DEFAULT_HSPACE: dict[str, float] = {"calendar": 0.2, "bar": 1.4}


def plot_from_file(
    filepath: str | Path,
    title: str = "Data Availability",
    date_column: str = "date",
    completeness_column: str = "completeness",
    kind: Literal["calendar", "bar"] = "calendar",
    hspace: float | None = None,
    cbar_bottom: int = 20,
    cbar_height: int = 10,
    tile_gap: float = 0.9,
    figsize_per_year: float | None = None,
    missing_color: str = "#e0e0e0",
    tile_shape: Literal["square", "squircle"] = "square",
    title_pad: int = 40,
    healthy_threshold: float = 90.0,
    status_colors: tuple[str, str, str] = ("#3fd15b", "#ffee00", "#f25c5c"),
    status_labels: tuple[str, str, str] = ("Healthy", "Issue", "Downtime"),
    bar_gap: float = 0.8,
) -> plt.Figure:
    """Build a data completeness figure from a file.

    Loads data from an Excel or CSV file and delegates to
    :func:`plot_from_df`. See :func:`plot_from_df` for the two figure kinds
    and the full parameter reference.

    Args:
        filepath: Path to an ``.xlsx``, ``.xls``, or ``.csv`` file accepted by
            :func:`~data_availability.data.load_data`.
        title: Figure super-title rendered above all subplots.
        date_column: Name of the datetime column in the file.
        completeness_column: Name of the numeric completeness column (0–100).
        kind: ``"calendar"`` for a GitHub-style heatmap; ``"bar"`` for a
            status-page style daily bar strip.
        hspace: Vertical spacing between year subplots.
        cbar_bottom: Calendar only. Gap in pixels between the last subplot and
            the colorbar.
        cbar_height: Calendar only. Height of the colorbar in pixels.
        tile_gap: Calendar only. Side length of each day tile.
        figsize_per_year: Figure height in inches per year subplot.
        missing_color: Color for calendar days absent from the input data.
        tile_shape: Calendar only. ``"square"`` or ``"squircle"``.
        title_pad: Gap in pixels between the first subplot and the
            super-title.
        healthy_threshold: Bar only. Minimum completeness for "healthy".
        status_colors: Bar only. Healthy, issue and downtime colors.
        status_labels: Bar only. Healthy, issue and downtime legend labels.
        bar_gap: Bar only. Width of each day bar.

    Returns:
        A :class:`matplotlib.figure.Figure`. The figure is not saved or
        displayed; call ``fig.savefig()`` or ``plt.show()`` afterwards.

    Raises:
        ValueError: If ``kind`` is not ``"calendar"`` or ``"bar"``.
    """
    df = load_data(
        filepath, date_column=date_column, completeness_column=completeness_column
    )
    return plot_from_df(
        df,
        title=title,
        date_column=date_column,
        completeness_column=completeness_column,
        kind=kind,
        hspace=hspace,
        cbar_bottom=cbar_bottom,
        cbar_height=cbar_height,
        tile_gap=tile_gap,
        figsize_per_year=figsize_per_year,
        missing_color=missing_color,
        tile_shape=tile_shape,
        title_pad=title_pad,
        healthy_threshold=healthy_threshold,
        status_colors=status_colors,
        status_labels=status_labels,
        bar_gap=bar_gap,
    )


def plot_from_df(
    df: pd.DataFrame,
    title: str = "Data Availability",
    date_column: str = "date",
    completeness_column: str = "completeness",
    kind: Literal["calendar", "bar"] = "calendar",
    hspace: float | None = None,
    cbar_bottom: int = 20,
    cbar_height: int = 10,
    tile_gap: float = 0.9,
    figsize_per_year: float | None = None,
    missing_color: str = "#e0e0e0",
    tile_shape: Literal["square", "squircle"] = "square",
    title_pad: int = 40,
    healthy_threshold: float = 90.0,
    status_colors: tuple[str, str, str] = ("#3fd15b", "#ffee00", "#f25c5c"),
    status_labels: tuple[str, str, str] = ("Healthy", "Issue", "Downtime"),
    bar_gap: float = 0.8,
) -> plt.Figure:
    """Build a data completeness figure from an in-memory DataFrame.

    Two figure kinds are available, both with one subplot per calendar year:

    - ``"calendar"``: GitHub-style heatmap. Each day is a tile on a
      Mon–Sun × week grid, colored on a red-yellow-green gradient, with a
      colorbar below the last subplot.
    - ``"bar"``: status-page style strip. Each day is a thin bar colored by
      status (healthy / issue / downtime), with a legend at the top right and
      the year as each subplot's title.

    Args:
        df: DataFrame with a datetime ``date_column`` and a numeric
            ``completeness_column`` (0–100), as returned by
            :func:`~data_availability.data.load_data`.
        title: Figure super-title rendered above all subplots.
        date_column: Name of the datetime column in ``df``.
        completeness_column: Name of the numeric completeness column (0–100).
        kind: ``"calendar"`` for a GitHub-style heatmap; ``"bar"`` for a
            status-page style daily bar strip.
        hspace: Vertical spacing between year subplots, passed to
            ``Figure.subplots_adjust``. Defaults to ``0.2`` for calendar and
            ``1.4`` for bar.
        cbar_bottom: Calendar only. Gap in pixels between the bottom edge of
            the last subplot and the top of the colorbar.
        cbar_height: Calendar only. Height of the colorbar in pixels.
        tile_gap: Calendar only. Side length of each day tile; values less
            than 1 add whitespace between tiles.
        figsize_per_year: Figure height in inches allocated per year subplot.
            Defaults to ``2.2`` for calendar and ``1.2`` for bar.
        missing_color: Hex or named color for calendar days absent from
            ``df``.
        tile_shape: Calendar only. ``"square"`` draws plain rectangles;
            ``"squircle"`` draws rectangles with rounded corners.
        title_pad: Gap in pixels between the top of the first subplot and the
            figure super-title.
        healthy_threshold: Bar only. Minimum completeness (0–100) for a day to
            count as healthy. Days with ``0`` completeness count as downtime;
            anything in between counts as an issue.
        status_colors: Bar only. Colors for the healthy, issue and downtime
            statuses.
        status_labels: Bar only. Legend labels for the healthy, issue and
            downtime statuses.
        bar_gap: Bar only. Width of each day bar; values less than 1 add
            whitespace between bars.

    Returns:
        A :class:`matplotlib.figure.Figure`. The figure is not saved or
        displayed; call ``fig.savefig()`` or ``plt.show()`` afterwards.

    Raises:
        ValueError: If ``kind`` is not ``"calendar"`` or ``"bar"``.
    """
    if kind not in _DEFAULT_FIGSIZE_PER_YEAR:
        raise ValueError(f"kind must be 'calendar' or 'bar', got {kind!r}")

    if figsize_per_year is None:
        figsize_per_year = _DEFAULT_FIGSIZE_PER_YEAR[kind]
    if hspace is None:
        hspace = _DEFAULT_HSPACE[kind]

    if kind == "bar":
        return _build_bar_figure(
            df,
            title=title,
            date_column=date_column,
            completeness_column=completeness_column,
            hspace=hspace,
            figsize_per_year=figsize_per_year,
            missing_color=missing_color,
            healthy_threshold=healthy_threshold,
            status_colors=status_colors,
            status_labels=status_labels,
            bar_gap=bar_gap,
            title_pad=title_pad,
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
        title_pad=title_pad,
    )

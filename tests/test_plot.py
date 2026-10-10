from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import numpy as np
import pandas as pd
import pytest
import matplotlib.pyplot as plt

from data_availability.plot import _NORM, plot_from_df, _resolve_color_scale

OUTPUT_DIR = Path(__file__).parent


def test_none_returns_continuous_scale():
    _, norm = _resolve_color_scale(None)
    assert norm is _NORM


def test_int_bins_map_to_discrete_colors():
    cmap, norm = _resolve_color_scale(5)
    np.testing.assert_allclose(norm.boundaries, [0, 20, 40, 60, 80, 100])
    assert cmap(norm(10)) == cmap(0)
    assert cmap(norm(100)) == cmap(4)
    assert cmap(norm(20)) == cmap(norm(39.9))
    assert cmap(norm(19.9)) != cmap(norm(20))


def test_custom_edges():
    cmap, norm = _resolve_color_scale([0, 50, 80, 100])
    assert norm.Ncmap == 3
    assert cmap.N == 3


@pytest.mark.parametrize(
    "bad",
    [1, 0, True, [0, 50], [0, 60, 40, 100], [10, 50, 100], [0, 50, 90]],
)
def test_invalid_bins_raise(bad):
    with pytest.raises(ValueError):
        _resolve_color_scale(bad)


@pytest.mark.parametrize("kind", ["calendar", "bar"])
def test_plot_with_color_bins(kind):
    dates = pd.date_range("2024-01-01", "2024-12-31", freq="D")
    rng = np.random.default_rng(0)
    df = pd.DataFrame({"date": dates, "completeness": rng.uniform(0, 100, len(dates))})

    fig = plot_from_df(df, kind=kind, color_bins=5)
    fig.savefig(OUTPUT_DIR / f"color_bins_{kind}.png", bbox_inches="tight")
    plt.close(fig)


@pytest.mark.parametrize("kind", ["calendar", "bar"])
def test_zero_completeness_renders_as_missing(kind):
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
            "completeness": [0.0, 50.0, 100.0],
        }
    )
    missing_color = "#123456"

    fig = plot_from_df(df, kind=kind, missing_color=missing_color)
    ax = fig.axes[0]
    missing_rgba = matplotlib.colors.to_rgba(missing_color)
    if kind == "bar":
        colors = [patch.get_facecolor() for patch in ax.patches]
    else:
        # Tiles are drawn column by column; Jan 1-3 2024 are Mon-Wed of week 0
        colors = [patch.get_facecolor() for patch in ax.patches[:3]]
    plt.close(fig)

    assert colors[0] == missing_rgba
    assert colors[1] != missing_rgba
    assert colors[2] != missing_rgba


def test_all_zero_completeness_raises():
    df = pd.DataFrame(
        {"date": pd.to_datetime(["2024-01-01"]), "completeness": [0.0]}
    )
    with pytest.raises(ValueError):
        plot_from_df(df)

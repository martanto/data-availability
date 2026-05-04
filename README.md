# data-availability

GitHub contribution-style calendar heatmaps for data completeness over time.

Useful for monitoring instrument data quality or any time-series availability tracking. Generates a matplotlib `Figure` with one subplot per calendar year, each day rendered as a color-coded tile on a red-yellow-green gradient.

**Input**: Excel (`.xlsx`/`.xls`) or CSV with `date` and `completeness` (0–100) columns.  
**Output**: A `matplotlib.figure.Figure` — save or display as needed.

![Availability of IJEN](https://raw.githubusercontent.com/martanto/data-availability/refs/heads/dev/init/assets/output.png)

## Installation

```bash
pip install data-availability
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add data-availability
```

## Quick start

### Fluent builder (recommended)

```python
import matplotlib.pyplot as plt
from data_availability import PlotAvailability

fig = (
    PlotAvailability("data.xlsx")
    .load_data(years="2023")
    .plot_availability(title="Sensor Uptime", tile_shape="squircle")
)
plt.savefig("availability.png", dpi=150, bbox_inches="tight")
```

### One-call helpers

```python
from data_availability import plot_from_file, plot_from_df

# From a file
fig = plot_from_file("data.csv", title="My Data")

# From a pre-loaded DataFrame
import pandas as pd
df = pd.read_csv("data.csv")
fig = plot_from_df(df, title="My Data")
```

## API reference

### `PlotAvailability(filepath)`

Fluent builder class.

```python
fig = (
    PlotAvailability("data.xlsx")
    .load_data(
        date_column="date",          # column name for dates
        completeness_column="completeness",  # column name for values (0–100)
        years=["2022", "2023"],      # filter to specific years (optional)
    )
    .plot_availability(
        title="Data Availability",
        tile_shape="square",         # "square" or "squircle"
        hspace=0.2,
        figsize_per_year=2.2,
        missing_color="#e0e0e0",
        cbar_bottom=20,
        cbar_height=10,
        tile_gap=0.9,
        title_pad=40,
    )
)
```

### `plot_from_file(filepath, **kwargs)` / `plot_from_df(df, **kwargs)`

Functional alternatives that accept the same keyword arguments as `.plot_availability()` plus `date_column` and `completeness_column`.

### `load_data(filepath, date_column, completeness_column)`

Load and normalize an Excel or CSV file into a DataFrame ready for plotting.

## Input format

| Column | Type | Notes |
|---|---|---|
| `date` | date string or datetime | parsed automatically |
| `completeness` | float | clipped to [0, 100]; strings replaced with NaN |

Column names are configurable via `date_column` / `completeness_column` parameters.

## Development

```bash
# Install with dev extras
uv sync --group dev

# Run the example
uv run main.py

# Lint and format
uv run ruff check --fix .
uv run ruff format .

# Type check
uv run ty check
```

## License

MIT © [Martanto](https://github.com/martanto)

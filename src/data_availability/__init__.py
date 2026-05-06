"""data-availability: GitHub-style calendar heatmaps for data completeness.

Generates matplotlib figures showing data completeness over time, one subplot
per calendar year, color-coded on a red-yellow-green gradient.

Example:
    >>> from data_availability import plot_from_file
    >>> fig = plot_from_file("data.csv", title="Sensor Uptime")
    >>> fig.savefig("availability.png", dpi=150)
"""

from importlib.metadata import version

from data_availability.data import load_data
from data_availability.plot import plot_from_df, plot_from_file
from data_availability.logger import configure_logging
from data_availability.availability import PlotAvailability
from data_availability.seismic.plot_seismic import PlotSeismicAvailability


__version__ = version("data-availability")
__author__ = "Martanto"
__author_email__ = "martanto@live.com"
__license__ = "MIT"
__copyright__ = "Copyright (c) 2026, Martanto"
__url__ = "https://github.com/martanto/data-availability"

__all__ = [
    "__version__",
    "__author__",
    "__author_email__",
    "__license__",
    "__copyright__",
    "PlotAvailability",
    "PlotSeismicAvailability",
    "configure_logging",
    "load_data",
    "plot_from_df",
    "plot_from_file",
]

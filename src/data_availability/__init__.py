from importlib.metadata import version

from data_availability.data import load_data
from data_availability.plot import plot_availability


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
    "load_data",
    "plot_availability",
]

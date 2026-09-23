"""Tests that every module in the package imports cleanly without circular imports.

Circular imports only surface when a module is the *first* one imported, so each
module is imported in a fresh interpreter (``sys.modules`` caching in a shared
process would mask the cycle).
"""

import pkgutil
import subprocess
import sys

import pytest

import data_availability


def _discover_modules() -> list[str]:
    """Return the dotted names of the package and all its submodules."""
    modules = [data_availability.__name__]
    for info in pkgutil.walk_packages(
        data_availability.__path__, prefix=f"{data_availability.__name__}."
    ):
        modules.append(info.name)
    return sorted(modules)


MODULES = _discover_modules()


def _import_in_fresh_interpreter(statement: str) -> subprocess.CompletedProcess:
    """Run an import statement in a new Python process."""
    return subprocess.run(
        [sys.executable, "-c", statement],
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_discovers_expected_modules():
    """Guard against discovery silently finding nothing."""
    expected = {
        "data_availability",
        "data_availability.availability",
        "data_availability.data",
        "data_availability.logger",
        "data_availability.plot",
        "data_availability.utils",
        "data_availability.seismic",
        "data_availability.seismic.sds",
        "data_availability.seismic.seismic_availability",
    }
    assert expected.issubset(MODULES)


@pytest.mark.parametrize("module", MODULES)
def test_module_imports_first_without_cycle(module: str):
    """Each module imports cleanly when it is the first module loaded."""
    result = _import_in_fresh_interpreter(f"import {module}")
    assert result.returncode == 0, (
        f"Importing {module!r} in a fresh interpreter failed:\n{result.stderr}"
    )


@pytest.mark.parametrize(
    "name",
    [
        "PlotAvailability",
        "SeismicAvailability",
        "configure_logging",
        "load_data",
        "plot_from_df",
        "plot_from_file",
    ],
)
def test_public_api_from_import(name: str):
    """Each public symbol is importable directly from the top-level package."""
    result = _import_in_fresh_interpreter(f"from data_availability import {name}")
    assert result.returncode == 0, (
        f"'from data_availability import {name}' failed:\n{result.stderr}"
    )


def test_all_matches_public_api():
    """Every name in ``__all__`` resolves on the package."""
    missing = [n for n in data_availability.__all__ if not hasattr(data_availability, n)]
    assert not missing, f"Names in __all__ not defined on package: {missing}"

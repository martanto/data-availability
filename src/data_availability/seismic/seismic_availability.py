from typing import Literal
from pathlib import Path
from datetime import datetime
from functools import cached_property
from multiprocessing import Pool

import pandas as pd
from matplotlib.figure import Figure

from data_availability.plot import plot_from_df
from data_availability.utils import to_datetime
from data_availability.logger import logger
from data_availability.seismic.sds import SDS


class SeismicAvailability:
    """Build a GitHub-style calendar heatmap from a SeisComP Data Structure (SDS) archive.

    Iterates over every day in ``[start_date, end_date]``, computes the
    completeness percentage for the given NSLC code via :class:`~data_availability.seismic.sds.SDS`,
    and delegates figure construction to :func:`~data_availability.plot.plot_from_df`.
    Parallel processing is supported through Python's :class:`multiprocessing.Pool`.

    Args:
        start_date: First date of the range in ``"YYYY-MM-DD"`` format.
        end_date: Last date of the range in ``"YYYY-MM-DD"`` format (inclusive).
        sds_dir: Root directory of the SDS archive.
        station: Station code (case-insensitive).
        channel: Channel code, e.g. ``"EHZ"`` (case-insensitive).
        network: Network code, e.g. ``"VG"`` (case-insensitive).
        location: Location code (case-insensitive).
        channel_type: SDS data-type qualifier. Defaults to ``"D"``.
        n_jobs: Number of parallel worker processes. Defaults to ``1`` (serial).
        verbose: When ``True``, emit detailed log messages during processing.

    Note:
        On Windows, Python's ``multiprocessing`` uses the ``spawn`` start method.
        When using ``n_jobs > 1`` in a script, wrap the call inside
        ``if __name__ == "__main__":`` to prevent recursive worker spawning.

    Example:
        >>> fig = (
        ...     SeismicAvailability(
        ...         start_date="2023-01-01",
        ...         end_date="2023-12-31",
        ...         sds_dir="/data/sds",
        ...         station="IJEN",
        ...         channel="EHZ",
        ...         network="VG",
        ...         location="00",
        ...         n_jobs=4,
        ...     )
        ...     .plot(title="IJEN EHZ Availability 2023")
        ... )
        >>> fig.savefig("ijen_availability.png", dpi=150, bbox_inches="tight")
    """

    def __init__(
        self,
        start_date: str,
        end_date: str,
        sds_dir: str,
        station: str,
        channel: str,
        network: str,
        location: str,
        channel_type: str = "D",
        n_jobs: int = 1,
        verbose: bool = False,
    ):
        self.start_date = to_datetime(start_date)
        self.end_date = to_datetime(end_date)
        self.dates = pd.date_range(self.start_date, self.end_date)
        self.sds = SDS(
            sds_dir=sds_dir,
            station=station,
            network=network,
            channel=channel,
            location=location,
            channel_type=channel_type,
            verbose=verbose,
        )
        self.df: pd.DataFrame = pd.DataFrame()
        self.n_jobs = max(n_jobs, 1)
        self.verbose = verbose

    def get_df(self) -> pd.DataFrame:
        """Compute completeness for every day in the date range.

        Runs jobs serially when ``n_jobs == 1``, or in parallel via
        :class:`multiprocessing.Pool` otherwise. Result is cached after the
        first call.

        Returns:
            DataFrame with ``nslc``, ``date``, ``filepath`` and
            ``completeness`` columns, one row per day in the range.
        """
        if not self.df.empty:
            return self.df

        if self.n_jobs == 1:
            results = [self._get_completeness(*job) for job in self._jobs]
        else:
            if self.verbose:
                logger.info(f"Running on {self.n_jobs} job(s)")

            with Pool(self.n_jobs) as pool:
                results = pool.starmap(self._get_completeness, self._jobs)

        if not results:
            raise ValueError("Data not found.")

        self.df = pd.DataFrame(results)
        return self.df

    @cached_property
    def _jobs(self) -> list[tuple[int, datetime]]:
        """Generate jobs for multiprocessing.

        Creates a list of (job_index, date) tuples for parallel processing,
        one per day in the date range.

        Returns:
            list[tuple[int, datetime]]: List of (job_index, date) tuples.

        Examples:
            >>> psa = SeismicAvailability(start_date="2025-01-01", end_date="2025-01-03", ...)
            >>> print(len(psa._jobs))  # 3 days
        """
        return [(job_index, date) for job_index, date in enumerate(self.dates)]

    def _get_completeness(self, job_index: int, date: datetime) -> dict:
        """Compute completeness for a single date (used as a pool worker target).

        Args:
            job_index: Sequential job index used for progress logging.
            date: Date for which to calculate completeness.

        Returns:
            A dict with ``"date"`` (datetime) and ``"completeness"`` (float) keys.
        """
        date_str = date.strftime("%Y-%m-%d")
        if self.verbose:
            logger.info(f"Running job {job_index}: {date_str}")
        return {
            "nslc": self.sds.nslc,
            "date": date,
            "filepath": self.sds.get_filepath(date),
            "completeness": self.sds.get_completeness(date),
        }

    def to_json(self) -> list[dict]:
        """Return completeness data as a list of records.

        Returns:
            List of dicts, each with ``"nslc"``, ``"date"``, ``"filepath"``
            and ``"completeness"`` keys, suitable for JSON serialisation.
        """
        return self.get_df().to_dict(orient="records")

    def to_excel(self, path: str | Path | None = None) -> Path:
        """Save the completeness DataFrame to an Excel file.

        Args:
            path: Destination path. Defaults to
                ``<nslc>_<start>-<end>.xlsx`` in the current working
                directory.

        Returns:
            The resolved destination path.
        """
        if path is None:
            suffix = f"{self.start_date.strftime('%Y-%m-%d')}-{self.end_date.strftime('%Y-%m-%d')}"
            path = Path(f"{self.sds.nslc}_{suffix}.xlsx")
        else:
            path = Path(path)
        self.get_df().to_excel(path, index=False)
        return path

    def plot(
        self,
        title: str | None = None,
        hspace: float = 0.2,
        cbar_bottom: int = 20,
        cbar_height: int = 10,
        tile_gap: float = 0.9,
        figsize_per_year: float = 2.2,
        missing_color: str = "#e0e0e0",
        tile_shape: Literal["square", "squircle"] = "square",
        title_pad: int = 40,
    ) -> Figure:
        """Compute seismic completeness and render a calendar heatmap.

        Calculates completeness for every day in the configured date range,
        then passes the resulting DataFrame to :func:`~data_availability.plot.plot_from_df`.
        Days with zero completeness are excluded from the figure so that
        no-data days render as ``missing_color`` rather than at the bottom
        of the color scale.

        Args:
            title: Figure super-title. Defaults to the NSLC string
                (e.g. ``"VG.IJEN.00.EHZ"``).
            hspace: Vertical spacing between year subplots.
            cbar_bottom: Gap in pixels between the bottom of the last subplot
                and the top of the colorbar.
            cbar_height: Height of the colorbar in pixels.
            tile_gap: Side length of each day tile; values less than 1 add
                whitespace between tiles.
            figsize_per_year: Figure height in inches allocated per year subplot.
            missing_color: Color for calendar days absent from the dataset.
            tile_shape: ``"square"`` for plain rectangles; ``"squircle"`` for
                rounded corners.
            title_pad: Gap in pixels between the top of the first subplot and
                the figure super-title.

        Returns:
            A :class:`matplotlib.figure.Figure` containing the heatmap.

        Raises:
            ValueError: If no completeness results are produced.
        """
        df = self.get_df()

        if df.empty:
            raise ValueError(f"No completeness results for {self.sds.nslc}")

        df = df[df["completeness"] > 0]

        return plot_from_df(
            df,
            title=title or self.sds.nslc,
            hspace=hspace,
            cbar_bottom=cbar_bottom,
            cbar_height=cbar_height,
            tile_gap=tile_gap,
            figsize_per_year=figsize_per_year,
            missing_color=missing_color,
            tile_shape=tile_shape,
            title_pad=title_pad,
        )

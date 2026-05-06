import os
from datetime import datetime

import numpy as np
from obspy import Trace, Stream, ObsPyReadingError, read

from data_availability.utils import to_datetime
from data_availability.logger import logger


class SDS:
    """Reader for seismic data stored in SeisComP Data Structure (SDS) format.

    SDS organises miniSEED files under a directory tree structured as
    ``<sds_dir>/<year>/<network>/<station>/<channel.type>/``.

    Args:
        sds_dir: Root directory of the SDS archive.
        station: Station code (case-insensitive, stored uppercased).
        channel: Channel code, e.g. ``"EHZ"`` (case-insensitive).
        network: Network code, e.g. ``"VG"`` (case-insensitive).
        location: Location code (case-insensitive).
        channel_type: SDS data-type qualifier. Defaults to ``"D"`` (waveform data).
        verbose: When ``True``, emit DEBUG/INFO log messages for each loaded file.

    Raises:
        FileNotFoundError: If ``sds_dir`` does not exist.
    """

    def __init__(
        self,
        sds_dir: str,
        station: str,
        channel: str,
        network: str,
        location: str,
        channel_type: str = "D",
        verbose: bool = False,
    ):
        self.sds_dir = sds_dir
        self.station = station.upper()
        self.channel = channel.upper()
        self.network = network.upper()
        self.location = location.upper()
        self.channel_type = channel_type.upper()
        self.verbose = verbose
        self.nslc = f"{self.network}.{self.station}.{self.location}.{self.channel}"

        if not os.path.exists(sds_dir):
            raise FileNotFoundError(f"Directory {sds_dir} does not exist")

    def get_filepath(self, date: datetime) -> str:
        """Return the expected miniSEED file path for a given date.

        Constructs the path following the SDS convention:
        ``<sds_dir>/<year>/<network>/<station>/<channel.type>/<nslc>.D.<year>.<julian_day>``.

        Args:
            date: Date for which to build the path.

        Returns:
            Absolute file path string (the file may or may not exist).
        """
        year = date.year
        julian_day = date.strftime("%j")

        # Construct SDS directory structure
        data_dir = os.path.join(
            self.sds_dir,
            str(year),
            self.network,
            self.station,
            f"{self.channel}.{self.channel_type}",
        )

        filename = f"{self.nslc}.D.{year}.{julian_day}"
        filepath = os.path.join(data_dir, filename)

        return filepath

    def load_stream(self, filepath: str, date_str: str) -> Stream:
        """Load seismic stream from miniSEED file.

        Reads the miniSEED file using ObsPy and merges any gaps using interpolation.

        Args:
            filepath (str): Absolute path to miniSEED file.
            date_str (str): Date string (YYYY-MM-DD) for logging purposes.

        Returns:
            Stream: ObsPy Stream object with traces merged, or an empty Stream
                if the file cannot be read.
        """
        try:
            stream = read(filepath, format="MSEED")
            stream = stream.merge(fill_value=None)

            if self.verbose:
                logger.debug(
                    f"{date_str} :: Loaded {len(stream)} trace(s) from {filepath}"
                )

            return stream

        except ObsPyReadingError as e:
            logger.error(f"{date_str} :: Failed to read miniSEED file: {filepath}")
            logger.error(f"{date_str} :: Error: {e}")
            return Stream()

        except Exception as e:
            logger.error(f"{date_str} :: Unexpected error loading {filepath}: {e}")
            return Stream()

    def get(self, date: str | datetime) -> Stream:
        """Load the seismic stream for a given date.

        Resolves the SDS path for ``date``, reads the miniSEED file, and merges
        any gap-separated traces. Missing or unreadable files are logged and an
        empty :class:`~obspy.core.stream.Stream` is returned.

        Args:
            date: Date to load, as a ``datetime`` object or ``"YYYY-MM-DD"`` string.

        Returns:
            An :class:`~obspy.core.stream.Stream` containing the merged trace(s),
            or an empty Stream when no data is available.
        """
        _date: datetime = to_datetime(date)
        date_str = _date.strftime("%Y-%m-%d")
        filepath = self.get_filepath(_date)

        # Check if file exists
        if not os.path.exists(filepath):
            if self.verbose:
                logger.debug(f"{date_str} :: miniSEED file not found: {filepath}")
            return Stream()

        # Load stream from file
        stream = self.load_stream(filepath, date_str)

        # Log results
        if len(stream) == 0:
            logger.warning(f"{date_str} :: No traces found in {filepath}")
        elif self.verbose:
            trace: Trace = stream[0]
            n_samples = len(trace.data)
            sampling_rate = trace.stats.sampling_rate
            duration = n_samples / sampling_rate if sampling_rate > 0 else 0

            logger.debug(f"{date_str} :: Stream loaded successfully")
            logger.info(
                f"{date_str} :: {len(stream)} trace(s), {n_samples} samples, "
                f"{duration:.1f}s duration @ {sampling_rate}Hz."
            )

        return stream

    def get_trace(self, date: datetime) -> Trace | None:
        """Retrieve a single Trace object for the given date.

        Loads the seismic stream for the specified date and returns its single
        merged trace. Returns None when no data is available.

        Args:
            date (datetime): Date for which to retrieve data.

        Returns:
            Trace | None: The merged Trace object, or None if no data is available.

        Raises:
            ValueError: If the stream contains more than one trace after merging.
        """
        stream = self.get(date)

        if len(stream) == 0:
            return None

        if len(stream) > 1:
            date_str = date.strftime("%Y-%m-%d")
            raise ValueError(
                f"{date_str} :: Stream has more than one trace ({len(stream)} trace(s)). "
                f"SDS should have only one trace after merge."
            )

        return stream[0]

    def get_completeness(self, date: datetime) -> float:
        """Calculate the data completeness percentage for a given date.

        Computes completeness as the fraction of non-zero samples relative to
        the expected daily sample count at the trace's sampling rate.

        Args:
            date: Date for which to compute completeness.

        Returns:
            Completeness percentage in the range [0, 100], rounded to two
            decimal places. Returns ``0.0`` when no data is available.
        """
        trace = self.get_trace(date)
        date_str = date.strftime("%Y-%m-%d")

        if trace is None:
            if self.verbose:
                logger.warning(f"{date_str} :: Completeness: 0.0%")
            return 0.0

        sampling_rate = trace.stats.sampling_rate
        daily_sampling_rate = sampling_rate * 60 * 60 * 24
        non_zero: float = np.round(
            (np.count_nonzero(trace.data) / daily_sampling_rate) * 100, 2
        )

        if self.verbose:
            logger.info(f"{date_str} :: Completeness: {non_zero}%")

        return float(non_zero)

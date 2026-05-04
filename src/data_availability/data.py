import warnings
from pathlib import Path

import numpy as np
import pandas as pd


def load_data(
    filepath: str | Path,
    date_column: str = "date",
    completeness_column: str = "completeness",
) -> pd.DataFrame:
    """Load and normalize availability data from an Excel or CSV file.

    Reads a file containing ``date`` and ``completeness`` columns, parses
    dates, clips completeness values to the range [0, 100], and returns the
    result sorted by date.

    Args:
        filepath: Path to an ``.xlsx``, ``.xls``, or ``.csv`` file.
        date_column: Name of the column to use as the date index. Defaults to
            ``"date"``.
        completeness_column: Name of the column to use as completeness values.
            Defaults to ``"completeness"``.

    Returns:
        A DataFrame with the selected date column (datetime64, time normalized
        to midnight) and completeness column (float, 0–100), sorted ascending
        by date with a reset integer index.

    Raises:
        FileNotFoundError: If ``filepath`` does not exist.
        KeyError: If the file is missing the specified date or completeness column.
        ValueError: If ``date`` values cannot be parsed as dates.
    """
    path = Path(filepath)
    if path.suffix in (".xlsx", ".xls"):
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)

    missing = [
        c for c in (date_column, completeness_column) if c not in df.columns.tolist()
    ]
    if missing:
        raise KeyError(f"Column(s) not found in file: {missing}")

    df = df[[date_column, completeness_column]].copy()

    df[date_column] = pd.to_datetime(df[date_column]).dt.normalize()
    if not isinstance(
        df[date_column].dtype, pd.DatetimeTZDtype
    ) and not pd.api.types.is_datetime64_any_dtype(df[date_column]):
        raise ValueError(
            f"Column '{date_column}' could not be parsed as DatetimeIndex."
        )

    string_mask = df[completeness_column].apply(lambda x: isinstance(x, str))
    if string_mask.any():
        n = string_mask.sum()
        warnings.warn(
            f"Column '{completeness_column}' contains {n} string value(s); replacing with NaN.",
            UserWarning,
            stacklevel=2,
        )
        df.loc[string_mask, completeness_column] = np.nan

    df[completeness_column] = pd.to_numeric(
        df[completeness_column], errors="coerce"
    ).clip(0, 100)

    return df.sort_values(date_column).reset_index(drop=True)

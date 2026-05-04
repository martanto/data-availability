from pathlib import Path

import pandas as pd


def load_data(filepath: str | Path) -> pd.DataFrame:
    """Load and normalize availability data from an Excel or CSV file.

    Reads a file containing ``date`` and ``completeness`` columns, parses
    dates, clips completeness values to the range [0, 100], and returns the
    result sorted by date.

    Args:
        filepath: Path to an ``.xlsx``, ``.xls``, or ``.csv`` file. Must
            contain ``date`` and ``completeness`` columns.

    Returns:
        A DataFrame with columns ``date`` (datetime64, time normalized to
        midnight) and ``completeness`` (float, 0–100), sorted ascending by
        date with a reset integer index.

    Raises:
        FileNotFoundError: If ``filepath`` does not exist.
        KeyError: If the file is missing a ``date`` or ``completeness`` column.
        ValueError: If ``date`` values cannot be parsed as dates.
    """
    path = Path(filepath)
    if path.suffix in (".xlsx", ".xls"):
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)

    df = df[["date", "completeness"]].copy()
    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    df["completeness"] = df["completeness"].clip(0, 100)

    return df.sort_values("date").reset_index(drop=True)

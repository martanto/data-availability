import os
from datetime import datetime


def to_datetime(date: str | datetime, variable_name: str | None = None) -> datetime:
    """Ensure date object is a datetime object.

    Converts date strings in YYYY-MM-DD format to datetime objects. If already a
    datetime object, returns it unchanged. Used for standardizing date inputs.

    Args:
        date (str | datetime): Date string in YYYY-MM-DD format or datetime object.
        variable_name (str | None, optional): Variable name for error messages.
            Defaults to None.

    Returns:
        datetime: Datetime object.

    Raises:
        ValueError: If date string is not in YYYY-MM-DD format.

    Examples:
        >>> to_datetime("2025-03-20")
        datetime.datetime(2025, 3, 20, 0, 0)
        >>> to_datetime(datetime(2025, 3, 20))
        datetime.datetime(2025, 3, 20, 0, 0)
    """
    if isinstance(date, datetime):
        return date

    variable_name = f"{variable_name}" if variable_name else "Date"

    try:
        return datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise ValueError(
            f"{variable_name} value {date} is not in valid YYYY-MM-DD format."
        )


def ensure_dir(path: str) -> str:
    """Create a directory (and any missing parents) if it does not already exist.

    A thin, named wrapper around ``os.makedirs(path, exist_ok=True)`` that
    returns the path so callers can chain it inline.

    Args:
        path (str): Directory path to create.

    Returns:
        str: The same ``path`` that was passed in.
    """
    os.makedirs(path, exist_ok=True)
    return path

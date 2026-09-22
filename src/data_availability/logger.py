import os
import sys

from loguru import logger

from data_availability.utils import ensure_dir


# Retention periods for log files.
_GENERAL_LOG_RETENTION = "30 days"
_ERROR_LOG_RETENTION = "90 days"

# Tracks whether logging is currently enabled.
_logging_enabled: bool = True

# Default log directory — not created until logging is first configured.
DEFAULT_LOG_DIR = os.path.join(os.getcwd(), "logs")

_FILE_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)

_CONSOLE_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)


def _add_console_handler(level: str = "INFO") -> None:
    """Add the stderr console handler at the given level."""
    logger.add(
        sys.stderr,
        format=_CONSOLE_FORMAT,
        level=level.upper(),
        colorize=True,
    )


# Enable console logging by default so callers see output out of the box.
# File logging is still opt-in via configure_logging() so the library never
# creates directories or writes files on import.
logger.remove()
_add_console_handler()


def _configure_handlers(log_dir: str, console_level: str = "INFO") -> None:
    """Remove all existing handlers and re-add console + file handlers.

    Centralises handler configuration so that module-level setup, set_log_level(),
    and set_log_directory() all use the same retention periods and formats.

    Args:
        log_dir (str): Directory path for log file output.
        console_level (str, optional): Log level for the console handler.
            Defaults to "INFO".
    """
    ensure_dir(log_dir)
    logger.remove()

    _add_console_handler(console_level)

    logger.add(
        os.path.join(log_dir, "availability_{time:YYYY-MM-DD}.log"),
        rotation="00:00",
        retention=_GENERAL_LOG_RETENTION,
        compression="zip",
        format=_FILE_FORMAT,
        level="DEBUG",
        enqueue=True,
    )

    logger.add(
        os.path.join(log_dir, "errors_{time:YYYY-MM-DD}.log"),
        rotation="00:00",
        retention=_ERROR_LOG_RETENTION,
        compression="zip",
        format=_FILE_FORMAT,
        level="ERROR",
        enqueue=True,
    )


def configure_logging(log_dir: str | None = None, console_level: str = "INFO") -> None:
    """Enable file + console logging for the package.

    Console logging is enabled automatically at import; call this to opt into
    file logging as well (rotating daily log + errors log) and to tune the
    console level. The log directory is created if it does not exist.

    Args:
        log_dir: Directory for log files. Defaults to ``./logs`` relative to the
            current working directory at call time.
        console_level: Log level for the console handler (default ``"INFO"``).
    """
    global DEFAULT_LOG_DIR
    if log_dir is not None:
        DEFAULT_LOG_DIR = os.path.abspath(log_dir)
    _configure_handlers(DEFAULT_LOG_DIR, console_level=console_level)


def get_logger():
    """Return the package-wide loguru logger instance.

    Returns:
        loguru.Logger: The configured logger instance with console and file handlers.
    """
    return logger


def set_log_level(level: str) -> None:
    """Change the console log level dynamically.

    Removes all existing handlers and re-adds them with the new console level.
    File handlers retain their original levels.

    Args:
        level (str): Desired log level for the console handler. One of
            ``"DEBUG"``, ``"INFO"``, ``"WARNING"``, ``"ERROR"``, or
            ``"CRITICAL"``. Case-insensitive.
    """
    _configure_handlers(DEFAULT_LOG_DIR, console_level=level)


def set_log_directory(log_dir: str) -> None:
    """Change the log file directory dynamically.

    Updates the global ``DEFAULT_LOG_DIR``, creates the directory if needed,
    then reconfigures all handlers to write to the new location.

    Args:
        log_dir (str): Absolute or relative path to the new log directory.
            Created automatically if it does not exist.
    """
    global DEFAULT_LOG_DIR
    DEFAULT_LOG_DIR = ensure_dir(os.path.abspath(log_dir))
    _configure_handlers(DEFAULT_LOG_DIR)
    logger.info(f"Log directory changed to: {DEFAULT_LOG_DIR}")


def disable_logging() -> None:
    """Disable all logging output globally.

    Remove all active loguru handlers so no messages are written to the
    console or log files. Call :func:`enable_logging` to restore handlers.
    """
    global _logging_enabled
    _logging_enabled = False
    os.environ["DISABLE_LOGGING"] = "1"
    logger.remove()


def enable_logging() -> None:
    """Re-enable console logging after a previous :func:`disable_logging` call.

    Restores the default console handler at ``INFO`` level. To also restore
    file handlers, call :func:`configure_logging` afterwards. Has no effect
    if logging is already enabled.
    """
    global _logging_enabled
    if not _logging_enabled:
        _logging_enabled = True
        os.environ.pop("DISABLE_LOGGING", None)
        _add_console_handler()

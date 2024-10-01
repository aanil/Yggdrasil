import logging

from datetime import datetime
from pathlib import Path

from lib.core_utils.config_loader import configs

# Suppress logging for specific noisy libraries
logging.getLogger("matplotlib").setLevel(logging.WARNING)
logging.getLogger("numba").setLevel(logging.WARNING)
logging.getLogger("h5py").setLevel(logging.WARNING)
logging.getLogger("PIL").setLevel(logging.WARNING)


def configure_logging(debug: bool = False) -> None:
    """Set up logging for the Yggdrasil application.

    Configures the logging environment by creating a log directory if it doesn't exist,
    setting the log file's path with a timestamp, and defining the log format and log level.

    Args:
        debug (bool, optional): If True, log messages will also be printed to the console.
            Defaults to False.

    Returns:
        None
    """
    log_dir = Path(configs["yggdrasil_log_dir"])
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H.%M.%S")
    log_file = log_dir / f"yggdrasil_{timestamp}.log"

    log_level = logging.DEBUG if debug else logging.INFO
    log_format = "%(asctime)s [%(name)s][%(levelname)s] %(message)s"

    # Configure logging with a file handler and optionally a console handler
    handlers = [logging.FileHandler(log_file)]
    if debug:
        handlers.append(logging.StreamHandler())

    logging.basicConfig(level=log_level, format=log_format, handlers=handlers)


def custom_logger(module_name: str) -> logging.Logger:
    """Create a custom logger for the specified module.
    
    Args:
        module_name (str): The name of the module for which the logger is created.

    Returns:
        logging.Logger: A custom logger for the specified module.
    """
    return logging.getLogger(module_name)
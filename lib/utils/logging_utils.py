import logging
# import appdirs
from datetime import datetime
from pathlib import Path

from lib.utils.config_loader import configs

logging.getLogger('matplotlib').setLevel(logging.WARNING)
logging.getLogger('numba').setLevel(logging.WARNING)
logging.getLogger('h5py').setLevel(logging.WARNING)

# def configure_logging(debug=False):
#     """
#     Set up logging for the Yggdrasil application.

#     This function configures the logging environment for the Yggdrasil application.
#     It creates a log directory if it doesn't exist, sets the log file's path with a
#     timestamp, and defines the log format and log level.

#     The log directory is determined by appdirs and is used to store log files.

#     Args:
#         debug (bool): If True, log messages will also be printed to the console.

#     Returns:
#         None
#     """
#     # Set up logging
#     # log_dir = Path(appdirs.user_log_dir("Yggdrasil", "NationalGenomicsInfrastructure"))
#     log_dir = Path(configs['yggdrasil_log_dir'])
#     log_dir.mkdir(parents=True, exist_ok=True)

#     # Add a timestamp to the log file name
#     timestamp = datetime.now().strftime("%Y-%m-%d_%H.%M.%S")
#     log_file = log_dir / f"yggdrasil_{timestamp}.log"

#     # Define log format
#     log_format = "%(asctime)s [%(levelname)s] %(message)s"
#     formatter = logging.Formatter(log_format)

#     # Set default logging level for all modules
#     logging.basicConfig(level=logging.INFO, format=log_format)

#     # Create a logger for the application
#     logger = logging.getLogger('Yggdrasil')
#     logger.propagate = False

#     # Set logging level for the application
#     log_level = logging.DEBUG if debug else logging.INFO
#     logger.setLevel(log_level)

#     # Create a file handler and set the log level and format
#     file_handler = logging.FileHandler(log_file)
#     file_handler.setLevel(log_level)
#     file_handler.setFormatter(formatter)

#     # Add the file handler to the logger
#     logger.addHandler(file_handler)

#     if debug:
#         # Create a console handler and set the log level and format
#         console_handler = logging.StreamHandler()
#         console_handler.setLevel(log_level)
#         console_handler.setFormatter(logging.Formatter(log_format))

#         # Add the console handler to the logger
#         logger.addHandler(console_handler)


# def custom_logger(name):
#     """
#     Create a custom logger for a specific module.

#     This function creates a custom logger for a specific module with the given name.

#     Args:
#         name (str): The name of the module for which the logger is created.

#     Returns:
#         logging.Logger: A custom logger for the specified module.
#     """
#     logger = logging.getLogger(name)
#     return logger

def configure_logging(debug=False):
    """
    Set up logging for the Yggdrasil application.
    """
    log_dir = Path(configs['yggdrasil_log_dir'])
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H.%M.%S")
    log_file = log_dir / f"yggdrasil_{timestamp}.log"

    log_level = logging.DEBUG if debug else logging.INFO
    log_format = "%(asctime)s [%(name)s][%(levelname)s] %(message)s"

    # Basic configuration that applies to all loggers
    logging.basicConfig(level=log_level, format=log_format, 
                        handlers=[logging.FileHandler(log_file), 
                                  logging.StreamHandler() if debug else None])
    
def custom_logger(module_name):
    """
    Create a custom logger for the specified module.
    
    Args:
        module_name (str): The name of the module for which the logger is created.

    Returns:
        logging.Logger: A custom logger for the specified module.
    """
    return logging.getLogger(module_name)
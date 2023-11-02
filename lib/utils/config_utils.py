import os
import sys
import json
import appdirs
import logging
import importlib

from pathlib import Path


# Module cache to store loaded modules
module_cache = {}

def load_module(module_path):
    """
    Load a module and cache it for reuse.
    """
    if module_path in module_cache:
        return module_cache[module_path]

    try:
        task_module = importlib.import_module(module_path)
        module_cache[module_path] = task_module
        return task_module
    except ImportError as e:
        print(f"Failed to load module '{module_path}': {e}")
        return None
    

def get_module_registry():
    """
    Load modules based on the configuration specified in a JSON file.

    Returns:
        dict: A dictionary mapping task types to their loaded modules and options.
    """

    # Get the full path to the configuration file
    module_config_path = get_config_file_path("module_registry.json")
    
    if module_config_path is not None:
        # Load configuration from JSON file
        with open(module_config_path, "r") as f:
            module_registry = json.load(f)
    else:
        # If the configuration file is not found, return an empty dictionary
        logging.warning("No module configuration file found.")


    # # Iterate through the task types and load their associated modules
    # for branch_name, branch in config.get("branches", {}).items():
    #     module_path = branch.get("module")
    #     options = branch.get("options", {})
        
    #     try:
    #         task_module = importlib.import_module(module_path)
    #         loaded_modules[branch_name] = {
    #             "module": task_module,
    #             "options": options
    #         }
    #     except ImportError as e:
    #         print(f"Failed to load module '{module_path}': {e}")

    return module_registry


def get_config_file_path(file_name):
    """
    Get the full path to a specific configuration file for the Yggdrasil application.

    This function constructs and returns the full path to the requested
    configuration file, including the directory obtained from appdirs.

    Args:
        filename (str): The name of the configuration file.

    Returns:
        pathlib.Path: A Path object representing the full path to the specified
            configuration file.
    """
    config_dir = Path(appdirs.user_config_dir("Yggdrasil", "NationalGenomicsInfrastructure"))
    config_file = config_dir / file_name

    # Check if the file exists, and return the full path if found
    if config_file.exists():
        return config_file
    else:
        logging.error(f"Configuration file '{file_name}' not found.")
        return None


def get_env_variable(variable_name, default=None):
    """
    Get the value of an environment variable.

    Args:
        variable_name (str): The name of the environment variable.
        default: A default value to return if the environment variable is not set.

    Returns:
        str or None: The value of the environment variable or the default value.
    """
    return os.environ.get(variable_name, default)


# Function to load configuration
def load_json_config(file_name="config.json", config_dir=None):
    """
    Load configuration from a JSON file.

    Returns:
        dict: Configuration settings or None on error.
    """
    if config_dir is None:
        config_file = get_config_file_path(file_name)
    else:
        config_file = Path(config_dir) / file_name

    try:
        with open(config_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"Config file not found: {config_file}")
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing config file '{config_file}': {e}")
    except TypeError as e:
        logging.error(f"Error parsing config file '{config_file}': {e}")

    return None
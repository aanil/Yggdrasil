import os
import appdirs
import logging
import importlib

from pathlib import Path

class YggdrasilUtilities:
    """
    Utility class for common functions in the Yggdrasil project.

    This class provides a collection of utility functions used across
    various modules in the Yggdrasil project. It includes functions
    for handling configurations, loading modules, and other common tasks.

    Attributes:
        None

    Methods:
        get_path(file_name: str) -> Path:
            Get the full path to a specific configuration or setup file
            for the Yggdrasil application, configured by appdirs.

        load_module(module_path: str) -> module:
            Load a module and cache it for reuse.

        env_variable(variable_name: str, default=None) -> str or None:
            Get the value of an environment variable.

    Usage:
        # Example Usage:
        utils = YggdrasilUtilities()
        config_path = utils.get_path("my_config.json")
        username = utils.env_variable("USERNAME")
    """
    module_cache = {}
    CONFIG_DIR = Path(__file__).parent.parent.parent / "yggdrasil_workspace/common/configurations"

    @staticmethod
    def load_realm_class(module_path):
        """
        Load a realm class from a module path and cache it for reuse. The module path should include
        the full path to the class in the format 'module.submodule.ClassName'.

        Args:
            module_path (str): The full path of the realm class to load (including the class name).

        Returns:
            class: The loaded realm class, or None if loading fails.
        """
        if module_path in YggdrasilUtilities.module_cache:
            return YggdrasilUtilities.module_cache[module_path]

        try:
            # Split the module path to get the module and class name
            module_name, class_name = module_path.rsplit('.', 1)
            module = importlib.import_module(module_name)
            realm_class = getattr(module, class_name)
            YggdrasilUtilities.module_cache[module_path] = realm_class
            return realm_class
        except (ImportError, AttributeError) as e:
            logging.error(f"Failed to load realm class from '{module_path}': {e}")
            return None

    @staticmethod
    def load_module(module_path):
        """
        Load a module and cache it for reuse.

        Args:
            module_path (str): The path of the module to load.

        Returns:
            module: The loaded module.
        """
        if module_path in YggdrasilUtilities.module_cache:
            return YggdrasilUtilities.module_cache[module_path]

        try:
            task_module = importlib.import_module(module_path)
            YggdrasilUtilities.module_cache[module_path] = task_module
            return task_module
        except ImportError as e:
            logging.error(f"Failed to load module '{module_path}': {e}")
            return None

    # @staticmethod
    # def get_path(file_name):
    #     """
    #     Get the full path to a specific configuration or setup file
    #     for the Yggdrasil application, configured by appdirs.

    #     Args:
    #         file_name (str): The name of the configuration file.

    #     Returns:
    #         pathlib.Path: A Path object representing the full path to the specified
    #             configuration file.
    #     """
    #     config_dir = Path(appdirs.user_config_dir("Yggdrasil", "NationalGenomicsInfrastructure"))
    #     config_file = config_dir / file_name
    #     if config_file.exists():
    #         return config_file
    #     else:
    #         logging.error(f"Configuration file '{file_name}' not found.")
    #         return None

    @staticmethod
    def get_path(file_name):
        """
        Get the full path to a specific configuration file for the Yggdrasil
        application from the centralized configurations directory.

        Args:
            file_name (str): The name of the configuration file.

        Returns:
            pathlib.Path: A Path object representing the full path to the specified
                configuration file, or None if the file is not found.
        """
        # Get the path to the configurations directory
        # config_dir = Path(__file__).parent.parent.parent / "configurations"
        config_dir = YggdrasilUtilities.CONFIG_DIR
        config_file = config_dir / file_name

        if config_file.exists():
            return config_file
        else:
            logging.error(f"Configuration file '{file_name}' not found.")
            return None


    @staticmethod
    def env_variable(variable_name, default=None):
        """
        Get the value of an environment variable.

        Args:
            variable_name (str): The name of the environment variable.
            default: A default value to return if the environment variable is not set.

        Returns:
            str or None: The value of the environment variable or the default value.
        """
        return os.environ.get(variable_name, default)


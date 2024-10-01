import os
import logging
import importlib

from pathlib import Path
from typing import Any, Dict, Optional, Type

class YggdrasilUtilities:
    """
    Utility class for common functions in the Yggdrasil project.

    Provides utility functions used across various modules, including
    configuration handling, module loading, and environment variable access.

    Attributes:
        module_cache (Dict[str, Any]): Cache for loaded modules and classes.
        CONFIG_DIR (Path): Directory containing configuration files.
    """
    module_cache: Dict[str, Any] = {}
    CONFIG_DIR: Path = Path(__file__).parent.parent.parent / "yggdrasil_workspace/common/configurations"

    @staticmethod
    def load_realm_class(module_path: str) -> Optional[Type]:
        """
        Load a realm class from a module path and cache it for reuse.
        
        The module path should include the full path to the class in the format
        'module.submodule.ClassName'.

        Args:
            module_path (str): The full path of the realm class to load (including the class name).

        Returns:
            Optional[Type]: The loaded realm class, or None if loading fails.
        """
        if module_path in YggdrasilUtilities.module_cache:
            return YggdrasilUtilities.module_cache[module_path]

        try:
            module_name, class_name = module_path.rsplit('.', 1)
            module = importlib.import_module(module_name)
            realm_class = getattr(module, class_name)
            YggdrasilUtilities.module_cache[module_path] = realm_class
            return realm_class
        except (ImportError, AttributeError) as e:
            logging.error(f"Failed to load realm class from '{module_path}': {e}")
            return None

    @staticmethod
    def load_module(module_path: str) -> Optional[Any]:
        """Load a module and cache it for reuse.

        Args:
            module_path (str): The path of the module to load.

        Returns:
            Optional[Any]: The loaded module, or None if loading fails.
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
        
    @staticmethod
    def get_path(file_name: str) -> Optional[Path]:
        """ Get the full path to a specific configuration file.

        Args:
            file_name (str): The name of the configuration file.

        Returns:
            Optional[Path]: A Path object representing the full path to the specified
                configuration file, or None if the file is not found.
        """
        config_file = YggdrasilUtilities.CONFIG_DIR / file_name

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
            default (Optional[str], optional): Default value if the environment variable
                is not set. Defaults to None.

        Returns:
            Optional[str]: The value of the environment variable or the default value.
        """
        return os.environ.get(variable_name, default)
    
    @staticmethod
    def get_last_processed_seq() -> str:
        """Retrieve the last processed sequence number from a file.

        Returns:
            str: The last processed sequence number.
        """
        seq_file = YggdrasilUtilities.get_path(".last_processed_seq")

        if seq_file.is_file():
            with open(seq_file, "r") as file:
                return file.read().strip()
        else:
            # Otherwise return a default sequence value of your choice.
            # NOTE: Zero (0) means start from the beginning. Note ideal!
            # TODO: Read default sequence value from configuration file.
            default_since = 0
            return default_since
        
    @staticmethod
    def save_last_processed_seq(last_processed_seq: str) -> None:
        """Save the last processed sequence number to a file.

        Args:
            last_processed_seq (str): The last processed sequence number to save.
        """
        seq_file = YggdrasilUtilities.get_path(".last_processed_seq")

        with open(seq_file, "w") as file:
            file.write(last_processed_seq)

import json
import types
import appdirs
import logging

from pathlib import Path

from lib.utils.common import YggdrasilUtilities as Ygg


class ConfigLoader:
    """
    Configuration loader for Yggdrasil.

    This class loads and manages configuration settings from a JSON file, providing an
    immutable view of the configuration data using MappingProxyType. It allows modules
    to access configuration settings without the ability to modify them.

    Args:
        file_name (str): The name of the configuration JSON file.

    Attributes:
        _config (dict): The loaded configuration data.
        config (types.MappingProxyType): An immutable view of the configuration data.

    Methods:
        load_config(): Load and validate the configuration from the JSON file.
        _config_file_path(file_name): Get the full path to a specific configuration file.
    """

    def __init__(self):
        # self._config = self._load_config(file_name, path)
        self._config = None

    def __getitem__(self, key):
        # Allow accessing configuration values using subscript notation
        return self._config.get(key)


    def load_config_path(self, path):
        """
        Load and validate the configuration from a JSON file given its full path.

        Args:
            path (str): The full path to the configuration JSON file.

        Returns:
            types.MappingProxyType: The loaded configuration data.
        """
        return self._load_config(path, path=True)


    def load_config(self, file_name):
        """
        Load and validate the configuration from a JSON file using appdirs.

        Args:
            file_name (str): The name of the configuration JSON file.

        Returns:
            types.MappingProxyType: The loaded configuration data.
        """
        return self._load_config(file_name, path=False)


    def _load_config(self, file_name, path=False):
        """
        Load and validate the configuration from the JSON file.

        Args:
            file_name (str): The name or path of the configuration JSON file.
            path (bool): True if file_name is a path, False if it's a filename.

        Returns:
            types.MappingProxyType: The loaded configuration data.
        """
        config_file = Path(file_name) if path else Ygg.get_path(file_name)

        if config_file is None:
            return {}  # Return an empty dictionary or handle the error as needed.

        config = {}
        try:
            with open(config_file, "r") as f:
                config = json.load(f)
                # Perform validation and error checking on the loaded data as needed.
                # ...

        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Error parsing config file '{config_file}': {e}")
        except TypeError as e:
            raise TypeError(f"Error parsing config file '{config_file}': {e}")

        self._config = types.MappingProxyType(config)

        return self._config



# Instantiate ConfigLoader when the module is imported
config_manager = ConfigLoader()
configs = config_manager.load_config("config.json")
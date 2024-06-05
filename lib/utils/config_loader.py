import json
import types

# NOTE: To use custom_logger resolve circular import issue
import logging

from pathlib import Path

from lib.utils.common import YggdrasilUtilities as Ygg

class ConfigLoader:
    """
    Configuration loader for Yggdrasil.

    This class loads and manages configuration settings from a JSON file, providing an
    immutable view of the configuration data using MappingProxyType. It allows modules
    to access configuration settings without the ability to modify them.

    Attributes:
        _config (types.MappingProxyType): The loaded configuration data.
    """

    def __init__(self):
        self._config = None

    def __getitem__(self, key):
        """
        Allow accessing configuration values using subscript notation.

        Args:
            key (str): The configuration key to retrieve the value for.

        Returns:
            The value associated with the specified key, or None if the key does not exist.
        """
        return self._config.get(key)


    def load_config_path(self, path):
        """
        Load and validate the configuration from a JSON file given its full path.

        Args:
            path (str): The full path to the configuration JSON file.

        Returns:
            types.MappingProxyType: The loaded configuration data.
        """
        return self._load_config(path, is_path=True)


    def load_config(self, file_name):
        """
        Load and validate the configuration from a JSON file.

        Args:
            file_name (str): The name of the configuration JSON file.

        Returns:
            types.MappingProxyType: The loaded configuration data.
        """
        return self._load_config(file_name, is_path=False)


    def _load_config(self, file_name, is_path=False):
        """
        Load and validate the configuration from the JSON file.

        Args:
            file_name (str): The name or path of the configuration JSON file.
            is_path (bool): True if file_name is a path, False if it's a filename.

        Returns:
            types.MappingProxyType: The loaded configuration data.
        """
        config_file = Path(file_name) if is_path else Ygg.get_path(file_name)

        if config_file is None:
            return types.MappingProxyType({})  # Return an empty dictionary  # Return an empty dictionary

        try:
            with open(config_file, "r") as f:
                config = json.load(f)
                # TODO: Perform validation and error checking on the loaded data if needed.
                self._config = types.MappingProxyType(config)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Error parsing config file '{config_file}': {e}")
        except TypeError as e:
            raise TypeError(f"Error parsing config file '{config_file}': {e}")
        except Exception as e:
            logging.error(f"Unexpected error loading config file '{config_file}': {e}")
            raise

        return self._config



# Instantiate ConfigLoader when the module is imported
config_manager = ConfigLoader()
configs = config_manager.load_config("config.json")
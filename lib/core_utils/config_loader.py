import json
import logging
import types
from pathlib import Path
from typing import Any, Mapping, Optional

from lib.core_utils.common import YggdrasilUtilities as Ygg

# NOTE: To use custom_logger resolve circular import issue


class ConfigLoader:
    """
    Configuration loader for Yggdrasil.

    This class loads and manages configuration settings from a JSON file, providing an
    immutable view of the configuration data using MappingProxyType. It allows modules
    to access configuration settings without the ability to modify them.

    Attributes:
        _config (Optional[Mapping[str, Any]]): The loaded configuration data.
    """

    def __init__(self) -> None:
        self._config: Optional[Mapping[str, Any]] = None

    def __getitem__(self, key: str) -> Any:
        """
        Allow accessing configuration values using subscript notation.

        Args:
            key (str): The configuration key to retrieve the value for.

        Returns:
            The value associated with the specified key, or None if the key does not exist.
        """
        return self._config.get(key) if self._config else None

    def load_config_path(self, path: str) -> Mapping[str, Any]:
        """
        Load and validate the configuration from a JSON file given its full path.

        Args:
            path (str): The full path to the configuration JSON file.

        Returns:
            Mapping[str, Any]: The loaded configuration data.
        """
        return self._load_config(path, is_path=True)

    def load_config(self, file_name: str) -> Mapping[str, Any]:
        """
        Load and validate the configuration from a JSON file.

        Args:
            file_name (str): The name of the configuration JSON file.

        Returns:
            Mapping[str, Any]: The loaded configuration data.
        """
        return self._load_config(file_name, is_path=False)

    def _load_config(self, file_name, is_path=False):
        """
        Load and validate the configuration from the JSON file.

        Args:
            file_name (str): The name or path of the configuration JSON file.
            is_path (bool): True if file_name is a path, False if it's a filename.

        Returns:
            Mapping[str, Any]: The loaded configuration data.
        """
        config_file = Path(file_name) if is_path else Ygg.get_path(file_name)

        if config_file is None:
            # Return an empty mapping if the file is not found
            self._config = types.MappingProxyType({})
            return self._config

        try:
            with open(config_file) as f:
                config = json.load(f)
                # TODO: Perform validation and error checking on the loaded data if needed.
                self._config = types.MappingProxyType(config)
        except json.JSONDecodeError as e:
            # Set config to empty immutable mapping before raising
            self._config = types.MappingProxyType({})
            raise json.JSONDecodeError(
                f"Error parsing config file '{config_file}': {e}", e.doc, e.pos
            )
        except TypeError as e:
            # Set config to empty immutable mapping before raising
            self._config = types.MappingProxyType({})
            raise TypeError(f"Error parsing config file '{config_file}': {e}")
        except Exception as e:
            logging.error(f"Unexpected error loading config file '{config_file}': {e}")
            # Set config to empty immutable mapping before raising
            self._config = types.MappingProxyType({})
            raise

        return self._config


# Instantiate ConfigLoader when the module is imported
config_manager = ConfigLoader()
configs = config_manager.load_config("config.json")

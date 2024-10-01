import unittest
from unittest.mock import patch, mock_open
from lib.core_utils.config_loader import ConfigLoader
from pathlib import Path
import types


class TestConfigLoader(unittest.TestCase):

    def setUp(self):
        self.config_loader = ConfigLoader()

    @patch('lib.utils.config_loader.Ygg.get_path', return_value=Path('dummy_file_path'))
    @patch('builtins.open', new_callable=mock_open, read_data='{"key": "value"}')
    @patch('json.load', return_value={"key": "value"})
    def test_load_config(self, mock_json_load, mock_file, mock_get_path):
        # Create an instance of the ConfigLoader class
        config_loader = ConfigLoader()
        # Call the load_config method
        config = config_loader.load_config('dummy_file_name')
        # Assert the Ygg.get_path function was called
        mock_get_path.assert_called_once_with('dummy_file_name')
        # Assert the file was opened
        mock_file.assert_called_once_with(Path('dummy_file_path'), 'r')
        # Assert the json.load function was called
        mock_json_load.assert_called_once()
        # Assert the config was loaded correctly
        self.assertEqual(config, types.MappingProxyType({"key": "value"}))


    @patch('builtins.open', new_callable=mock_open, read_data='{"key": "value"}')
    @patch('json.load', return_value={"key": "value"})
    def test_load_config_path(self, mock_json_load, mock_file):
        # Call the load_config_path method
        config = self.config_loader.load_config_path('/path/to/config.json')
        # Assert the file was opened
        mock_file.assert_called_once_with(Path('/path/to/config.json'), 'r')
        # Assert the json.load function was called
        mock_json_load.assert_called_once()
        # Assert the config was loaded correctly
        self.assertEqual(config, types.MappingProxyType({"key": "value"}))

    def test_getitem(self):
        # Load some configuration data
        self.config_loader._config = types.MappingProxyType({"key": "value"})
        # Call the __getitem__ method
        value = self.config_loader["key"]
        # Assert the correct value was returned
        self.assertEqual(value, "value")

    def test_getitem(self):
        # Mock the _config dictionary
        self.config_loader._config = types.MappingProxyType({"key": "value"})
        # Call the __getitem__ method
        value = self.config_loader["key"]
        # Assert the correct value was returned
        self.assertEqual(value, "value")


if __name__ == "__main__":
    unittest.main()

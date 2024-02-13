import unittest
from unittest.mock import patch, MagicMock
from lib.utils.logging_utils import configure_logging

class TestConfigureLogging(unittest.TestCase):
    @patch('lib.utils.logging_utils.logging')
    @patch('lib.utils.logging_utils.appdirs')
    @patch('lib.utils.logging_utils.datetime')
    @patch('lib.utils.logging_utils.Path')
    def test_configure_logging(self, mock_path, mock_datetime, mock_appdirs, mock_logging):
        # Set up the mocks
        mock_path.return_value.mkdir.return_value = None
        mock_appdirs.user_log_dir.return_value = '/path/to/logs'
        mock_datetime.now.return_value.strftime.return_value = '2022-01-01_00.00.00'
        mock_logging.DEBUG = 10
        mock_logging.INFO = 20
        mock_logging.getLogger.return_value = MagicMock()

        # Call the function
        configure_logging(debug=True)

        # Assert the mocks were called correctly
        mock_path.assert_called_once_with('/path/to/logs')
        mock_path.return_value.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_datetime.now.assert_called_once()
        mock_datetime.now.return_value.strftime.assert_called_once_with("%Y-%m-%d_%H.%M.%S")
        mock_logging.getLogger.assert_called_once()
        mock_logging.getLogger.return_value.setLevel.assert_called_once_with(10)
        mock_logging.getLogger.return_value.addHandler.assert_called()

        # Call the function again with debug=False
        configure_logging(debug=False)

        # Assert the logger's level was set to INFO
        mock_logging.getLogger.return_value.setLevel.assert_called_with(20)

if __name__ == '__main__':
    unittest.main()
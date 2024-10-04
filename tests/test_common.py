import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from lib.core_utils.common import YggdrasilUtilities


class TestYggdrasilUtilities(unittest.TestCase):

    @patch("lib.utils.common.importlib.import_module")
    def test_load_realm_class_success(self, mock_import_module):
        # Mock successful class loading
        mock_module = MagicMock()
        mock_class = MagicMock()
        mock_import_module.return_value = mock_module
        mock_module.MyClass = mock_class

        result = YggdrasilUtilities.load_realm_class("my_module.MyClass")

        mock_import_module.assert_called_once_with("my_module")
        self.assertEqual(result, mock_class)

    @patch("lib.utils.common.importlib.import_module")
    def test_load_realm_class_failure(self, mock_import_module):
        # Mock import error
        mock_import_module.side_effect = ImportError()

        result = YggdrasilUtilities.load_realm_class("non_existent_module.MyClass")

        mock_import_module.assert_called_once_with("non_existent_module")
        self.assertIsNone(result)

    @patch("lib.utils.common.importlib.import_module")
    def test_load_module_success(self, mock_import_module):
        # Mock successful module loading
        mock_module = MagicMock()
        mock_import_module.return_value = mock_module

        result = YggdrasilUtilities.load_module("my_module")

        mock_import_module.assert_called_once_with("my_module")
        self.assertEqual(result, mock_module)

    @patch("lib.utils.common.importlib.import_module")
    def test_load_module_failure(self, mock_import_module):
        # Mock import error
        mock_import_module.side_effect = ImportError()

        result = YggdrasilUtilities.load_module("non_existent_module")

        mock_import_module.assert_called_once_with("non_existent_module")
        self.assertIsNone(result)

    @patch("lib.utils.common.Path.exists")
    def test_get_path_file_exists(self, mock_exists):
        # Your input needed: Adjust the file path according to your project structure
        mock_exists.return_value = True
        expected_path = Path(
            "/home/anastasios/Documents/git/Yggdrasil/yggdrasil_workspace/common/configurations/config.json"
        )  # Replace with actual expected path

        result = YggdrasilUtilities.get_path("config.json")

        self.assertIsNotNone(result)
        self.assertEqual(result, expected_path)

    @patch("lib.utils.common.Path.exists")
    def test_get_path_file_not_exists(self, mock_exists):
        mock_exists.return_value = False

        result = YggdrasilUtilities.get_path("config.json")

        self.assertIsNone(result)

    @patch.dict("lib.utils.common.os.environ", {"MY_VAR": "value"})
    def test_env_variable_exists(self):
        result = YggdrasilUtilities.env_variable("MY_VAR")
        self.assertEqual(result, "value")

    @patch.dict("lib.utils.common.os.environ", {}, clear=True)
    def test_env_variable_not_exists(self):
        result = YggdrasilUtilities.env_variable("MY_VAR", default="default")
        self.assertEqual(result, "default")

    # TODO: Additional test cases or scenarios


if __name__ == "__main__":
    unittest.main()

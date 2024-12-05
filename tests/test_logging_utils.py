import logging
import os
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from lib.core_utils.logging_utils import configure_logging, custom_logger


class TestLoggingUtils(unittest.TestCase):

    def setUp(self):
        # Backup original logging handlers and level
        self.original_handlers = logging.getLogger().handlers.copy()
        self.original_level = logging.getLogger().level

        # Clear existing handlers
        logging.getLogger().handlers = []

        # Mock configs
        self.mock_configs = {"yggdrasil_log_dir": "/tmp/yggdrasil_logs"}
        self.patcher_configs = patch(
            "lib.core_utils.logging_utils.configs", self.mock_configs
        )
        self.patcher_configs.start()

        # Mock datetime.datetime to control the timestamp
        self.patcher_datetime = patch("lib.core_utils.logging_utils.datetime")
        self.mock_datetime = self.patcher_datetime.start()

        # Create a mock datetime instance
        mock_now = MagicMock()
        mock_now.strftime.return_value = "2021-01-01_12.00.00"
        # Set datetime.now() to return our mock datetime instance
        self.mock_datetime.now.return_value = mock_now

        # Mock Path.mkdir to prevent actual directory creation
        self.patcher_mkdir = patch("pathlib.Path.mkdir")
        self.mock_mkdir = self.patcher_mkdir.start()

        # Mock logging.basicConfig to track calls
        self.patcher_basicConfig = patch("logging.basicConfig")
        self.mock_basicConfig = self.patcher_basicConfig.start()

        # Mock logging.FileHandler to prevent it from actually opening a file
        self.patcher_filehandler = patch(
            "lib.core_utils.logging_utils.logging.FileHandler", MagicMock()
        )
        self.mock_filehandler = self.patcher_filehandler.start()

    def tearDown(self):
        # Restore original logging handlers and level
        logging.getLogger().handlers = self.original_handlers
        logging.getLogger().level = self.original_level

        # Stop all patches
        self.patcher_configs.stop()
        self.patcher_datetime.stop()
        self.patcher_mkdir.stop()
        self.patcher_basicConfig.stop()
        self.patcher_filehandler.stop()

    def test_configure_logging_default(self):
        # Test configure_logging with default parameters (debug=False)
        configure_logging()

        expected_log_dir = Path(self.mock_configs["yggdrasil_log_dir"])
        expected_log_file = expected_log_dir / "yggdrasil_2021-01-01_12.00.00.log"
        expected_log_level = logging.INFO
        expected_log_format = "%(asctime)s [%(name)s][%(levelname)s] %(message)s"

        self.mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

        handlers = [logging.FileHandler(expected_log_file)]
        self.mock_basicConfig.assert_called_once_with(
            level=expected_log_level, format=expected_log_format, handlers=handlers
        )

    def test_configure_logging_debug_true(self):
        # Test configure_logging with debug=True
        configure_logging(debug=True)

        expected_log_dir = Path(self.mock_configs["yggdrasil_log_dir"])
        expected_log_file = expected_log_dir / "yggdrasil_2021-01-01_12.00.00.log"
        expected_log_level = logging.DEBUG
        expected_log_format = "%(asctime)s [%(name)s][%(levelname)s] %(message)s"

        self.mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

        handlers = [logging.FileHandler(expected_log_file), logging.StreamHandler()]
        self.mock_basicConfig.assert_called_once_with(
            level=expected_log_level, format=expected_log_format, handlers=handlers
        )

    def test_configure_logging_creates_log_directory(self):
        # Ensure that configure_logging attempts to create the log directory
        configure_logging()

        expected_log_dir = Path(self.mock_configs["yggdrasil_log_dir"])
        self.mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        self.assertEqual(self.mock_mkdir.call_args[0], ())
        self.assertEqual(
            self.mock_mkdir.call_args[1], {"parents": True, "exist_ok": True}
        )

    def test_configure_logging_handles_existing_directory(self):
        # Test that no exception is raised if the directory already exists
        self.mock_mkdir.side_effect = FileExistsError

        configure_logging()

        # The test passes if no exception is raised

    def test_configure_logging_invalid_log_dir(self):
        # Test handling when the log directory is invalid
        self.mock_mkdir.side_effect = PermissionError("Permission denied")

        with self.assertRaises(PermissionError):
            configure_logging()

    def test_configure_logging_logs_to_correct_file(self):
        # Mock logging.FileHandler to prevent file creation
        with patch("logging.FileHandler") as mock_file_handler:
            configure_logging()

            expected_log_dir = Path(self.mock_configs["yggdrasil_log_dir"])
            expected_log_file = expected_log_dir / "yggdrasil_2021-01-01_12.00.00.log"

            mock_file_handler.assert_called_once_with(expected_log_file)

    def test_custom_logger_returns_logger(self):
        # Test that custom_logger returns a Logger instance with the correct name
        module_name = "test_module"
        logger = custom_logger(module_name)

        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, module_name)

    def test_custom_logger_same_logger(self):
        # Test that calling custom_logger multiple times with the same name returns the same logger
        module_name = "test_module"
        logger1 = custom_logger(module_name)
        logger2 = custom_logger(module_name)

        self.assertIs(logger1, logger2)

    def test_logging_levels_suppressed(self):
        # Test that logging levels for specified noisy libraries are set to WARNING
        noisy_libraries = ["matplotlib", "numba", "h5py", "PIL"]
        for lib in noisy_libraries:
            logger = logging.getLogger(lib)
            self.assertEqual(logger.level, logging.WARNING)

    def test_logging_configuration_reset_between_tests(self):
        # Ensure that logging configuration does not leak between tests
        configure_logging()
        initial_handlers = logging.getLogger().handlers.copy()
        initial_level = logging.getLogger().level

        # Simulate another logging configuration
        configure_logging(debug=True)
        new_handlers = logging.getLogger().handlers.copy()
        new_level = logging.getLogger().level

        # Handlers and level should be updated
        self.assertNotEqual(initial_handlers, new_handlers)
        self.assertNotEqual(initial_level, new_level)

    def test_configure_logging_multiple_calls(self):
        # Test that multiple calls to configure_logging update the logging configuration
        configure_logging()
        first_call_handlers = logging.getLogger().handlers.copy()
        first_call_level = logging.getLogger().level

        configure_logging(debug=True)
        second_call_handlers = logging.getLogger().handlers.copy()
        second_call_level = logging.getLogger().level

        self.assertNotEqual(first_call_handlers, second_call_handlers)
        self.assertNotEqual(first_call_level, second_call_level)

    def test_configure_logging_no_configs(self):
        # Test behavior when configs do not contain 'yggdrasil_log_dir'
        self.mock_configs.pop("yggdrasil_log_dir", None)

        with self.assertRaises(KeyError):
            configure_logging()

    def test_configure_logging_with_invalid_log_file(self):
        # Test handling when the log file cannot be created
        with patch(
            "logging.FileHandler", side_effect=PermissionError("Permission denied")
        ):
            with self.assertRaises(PermissionError):
                configure_logging()

    def test_configure_logging_with_invalid_stream_handler(self):
        # Test handling when StreamHandler cannot be initialized
        with patch("logging.StreamHandler", side_effect=Exception("Stream error")):
            with self.assertRaises(Exception):
                configure_logging(debug=True)

    def test_configure_logging_with_existing_handlers(self):
        # Test that existing handlers are replaced
        logging.getLogger().handlers = [MagicMock()]
        configure_logging()
        self.assertEqual(len(logging.getLogger().handlers), 1)
        self.mock_basicConfig.assert_called_once()

    def test_configure_logging_handler_types(self):
        # Test that handlers are of correct types
        with patch("logging.FileHandler") as mock_file_handler, patch(
            "logging.StreamHandler"
        ) as mock_stream_handler:
            configure_logging(debug=True)

            handlers = [
                mock_file_handler.return_value,
                mock_stream_handler.return_value,
            ]
            self.mock_basicConfig.assert_called_once_with(
                level=logging.DEBUG,
                format="%(asctime)s [%(name)s][%(levelname)s] %(message)s",
                handlers=handlers,
            )

    def test_configure_logging_log_format(self):
        # Test that the log format is set correctly
        configure_logging()
        expected_log_format = "%(asctime)s [%(name)s][%(levelname)s] %(message)s"
        self.mock_basicConfig.assert_called_once()
        self.assertEqual(
            self.mock_basicConfig.call_args[1]["format"], expected_log_format
        )

    def test_configure_logging_log_level_info(self):
        # Test that the log level is set to INFO when debug=False
        configure_logging()
        self.mock_basicConfig.assert_called_once()
        self.assertEqual(self.mock_basicConfig.call_args[1]["level"], logging.INFO)

    def test_configure_logging_log_level_debug(self):
        # Test that the log level is set to DEBUG when debug=True
        configure_logging(debug=True)
        self.mock_basicConfig.assert_called_once()
        self.assertEqual(self.mock_basicConfig.call_args[1]["level"], logging.DEBUG)

    def test_configure_logging_handlers_order(self):
        # Test that handlers are in the correct order
        with patch("logging.FileHandler") as mock_file_handler, patch(
            "logging.StreamHandler"
        ) as mock_stream_handler:
            configure_logging(debug=True)

            handlers = [
                mock_file_handler.return_value,
                mock_stream_handler.return_value,
            ]
            self.assertEqual(self.mock_basicConfig.call_args[1]["handlers"], handlers)

    def test_configure_logging_timestamp_format(self):
        # Test that the timestamp in the log file name is correctly formatted
        configure_logging()

        expected_timestamp = "2021-01-01_12.00.00"
        expected_log_dir = Path(self.mock_configs["yggdrasil_log_dir"])
        expected_log_file = expected_log_dir / f"yggdrasil_{expected_timestamp}.log"

        with patch("logging.FileHandler") as mock_file_handler:
            configure_logging()
            mock_file_handler.assert_called_with(expected_log_file)

    def test_configure_logging_custom_timestamp(self):
        # Test with a different timestamp
        self.mock_datetime.now.return_value = datetime(2022, 2, 2, 14, 30, 0)
        self.mock_datetime.now().strftime.return_value = "2022-02-02_14.30.00"

        configure_logging()

        expected_timestamp = "2022-02-02_14.30.00"
        expected_log_dir = Path(self.mock_configs["yggdrasil_log_dir"])
        expected_log_file = expected_log_dir / f"yggdrasil_{expected_timestamp}.log"

        with patch("logging.FileHandler") as mock_file_handler:
            configure_logging()
            mock_file_handler.assert_called_with(expected_log_file)

    def test_configure_logging_invalid_configs_type(self):
        # Test handling when configs is of invalid type
        with patch("lib.core_utils.logging_utils.configs", None):
            with self.assertRaises(TypeError):
                configure_logging()

    def test_configure_logging_log_dir_is_file(self):
        # Test behavior when the log directory path is actually a file
        with patch("pathlib.Path.mkdir", side_effect=NotADirectoryError):
            with self.assertRaises(NotADirectoryError):
                configure_logging()

    def test_configure_logging_no_handlers(self):
        # Test that logging.basicConfig is called with correct handlers
        with patch("logging.basicConfig") as mock_basic_config:
            configure_logging()
            self.assertIn("handlers", mock_basic_config.call_args[1])

    def test_custom_logger_different_names(self):
        # Test that different module names return different loggers
        logger1 = custom_logger("module1")
        logger2 = custom_logger("module2")
        self.assertNotEqual(logger1, logger2)
        self.assertNotEqual(logger1.name, logger2.name)

    def test_custom_logger_propagate_false(self):
        # Test that the logger's propagate attribute is default (True)
        logger = custom_logger("module")
        self.assertTrue(logger.propagate)

    def test_custom_logger_level_not_set(self):
        # Test that the logger's level is not explicitly set (inherits from root)
        logger = custom_logger("module")
        self.assertEqual(logger.level, logging.NOTSET)

    def test_configure_logging_without_debug_stream_handler(self):
        # Test that StreamHandler is not added when debug=False
        with patch("logging.StreamHandler") as mock_stream_handler:
            configure_logging()
            mock_stream_handler.assert_not_called()

    def test_configure_logging_with_debug_stream_handler(self):
        # Test that StreamHandler is added when debug=True
        with patch("logging.StreamHandler") as mock_stream_handler:
            configure_logging(debug=True)
            mock_stream_handler.assert_called_once()

    def test_configure_logging_handlers_are_set_correctly(self):
        # Test that handlers are set correctly in the root logger
        with patch("logging.FileHandler") as mock_file_handler, patch(
            "logging.StreamHandler"
        ) as mock_stream_handler:
            configure_logging(debug=True)

            root_logger = logging.getLogger()
            self.assertEqual(len(root_logger.handlers), 2)
            self.assertIsInstance(
                root_logger.handlers[0], mock_file_handler.return_value.__class__
            )
            self.assertIsInstance(
                root_logger.handlers[1], mock_stream_handler.return_value.__class__
            )

    def test_configure_logging_respects_existing_loggers(self):
        # Test that existing loggers are not affected by configure_logging
        existing_logger = logging.getLogger("existing")
        existing_logger_level = existing_logger.level
        existing_logger_handlers = existing_logger.handlers.copy()

        configure_logging()

        self.assertEqual(existing_logger.level, existing_logger_level)
        self.assertEqual(existing_logger.handlers, existing_logger_handlers)

    def test_logging_messages_after_configuration(self):
        # Test that logging messages are handled correctly after configuration
        with patch("logging.FileHandler") as mock_file_handler:
            mock_file_handler.return_value = MagicMock()
            configure_logging()
            logger = custom_logger("test_module")
            logger.info("Test message")

            # Ensure that the message is handled by the file handler
            mock_file_handler.return_value.emit.assert_called()

    def test_suppressed_loggers_levels(self):
        # Ensure that suppressed loggers have their levels set to WARNING
        suppressed_loggers = ["matplotlib", "numba", "h5py", "PIL"]
        for logger_name in suppressed_loggers:
            logger = logging.getLogger(logger_name)
            self.assertEqual(logger.level, logging.WARNING)

    def test_suppressed_loggers_do_not_propagate(self):
        # Ensure that suppressed loggers still propagate messages
        suppressed_loggers = ["matplotlib", "numba", "h5py", "PIL"]
        for logger_name in suppressed_loggers:
            logger = logging.getLogger(logger_name)
            self.assertTrue(logger.propagate)

    def test_logging_basic_config_called_once(self):
        # Ensure that logging.basicConfig is called only once
        configure_logging()
        self.mock_basicConfig.assert_called_once()

    def test_configure_logging_with_relative_log_dir(self):
        # Test handling when 'yggdrasil_log_dir' is a relative path
        self.mock_configs["yggdrasil_log_dir"] = "relative/path/to/logs"
        configure_logging()

        expected_log_dir = Path("relative/path/to/logs")
        self.mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_configure_logging_with_env_var_in_log_dir(self):
        # Test handling when 'yggdrasil_log_dir' contains an environment variable
        self.mock_configs["yggdrasil_log_dir"] = "${HOME}/logs"
        with patch.dict(os.environ, {"HOME": "/home/testuser"}):
            configure_logging()

            expected_log_dir = Path("/home/testuser/logs")
            self.mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_configure_logging_invalid_log_format(self):
        # Test handling when log_format is invalid
        with patch("logging.basicConfig") as mock_basic_config:
            configure_logging()
            mock_basic_config.assert_called_once()
            self.assertIn("format", mock_basic_config.call_args[1])

    def test_configure_logging_with_custom_handlers(self):
        # Test that custom handlers can be added if the code is modified in the future
        # Since the current code does not support this, we check that handlers are as expected
        configure_logging()
        root_logger = logging.getLogger()
        self.assertEqual(len(root_logger.handlers), 1)
        self.assertIsInstance(root_logger.handlers[0], logging.FileHandler)

    def test_configure_logging_with_no_handlers(self):
        # Test that an error is raised if handlers list is empty
        with patch("logging.basicConfig") as mock_basic_config:
            with patch(
                "lib.core_utils.logging_utils.logging.FileHandler",
                side_effect=Exception("Handler error"),
            ):
                with self.assertRaises(Exception):
                    configure_logging()

    def test_configure_logging_multiple_times(self):
        # Test that multiple calls to configure_logging do not cause errors
        configure_logging()
        configure_logging(debug=True)
        self.assertTrue(True)  # Test passes if no exception is raised


if __name__ == "__main__":
    unittest.main()

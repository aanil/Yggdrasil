import sys
import unittest
from io import StringIO
from unittest.mock import Mock, call, patch

from yggdrasil.cli import main


class TestYggdrasilCLI(unittest.TestCase):
    """
    Comprehensive tests for Yggdrasil CLI - the application entry point.

    Tests argument parsing, mode selection, configuration loading, session management,
    daemon mode, run-doc mode, error handling, and integration scenarios.
    """

    def setUp(self):
        """Set up test fixtures and reset global state."""
        # Reset YggSession state before each test
        from lib.core_utils.ygg_session import YggSession

        YggSession._YggSession__dev_mode = False  # type: ignore
        YggSession._YggSession__dev_already_set = False  # type: ignore
        YggSession._YggSession__manual_submit = False  # type: ignore
        YggSession._YggSession__manual_already_set = False  # type: ignore

        # Store original sys.argv
        self.original_argv = sys.argv.copy()

        # Mock objects that will be used across tests
        self.mock_config = {"test": "config", "couchdb_poll_interval": 5}

    def tearDown(self):
        """Clean up after each test."""
        # Restore original sys.argv
        sys.argv = self.original_argv

        # Reset YggSession state
        from lib.core_utils.ygg_session import YggSession

        YggSession._YggSession__dev_mode = False  # type: ignore
        YggSession._YggSession__dev_already_set = False  # type: ignore
        YggSession._YggSession__manual_submit = False  # type: ignore
        YggSession._YggSession__manual_already_set = False  # type: ignore

    # =====================================================
    # ARGUMENT PARSING TESTS
    # =====================================================

    def test_no_arguments_shows_help(self):
        """Test that running without arguments shows help and returns."""
        sys.argv = ["yggdrasil"]

        # Capture stdout to verify help is printed
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            main()

        # Verify help was printed (should contain usage information)
        stdout_content = mock_stdout.getvalue()
        self.assertIn("usage: yggdrasil", stdout_content)
        self.assertIn("daemon", stdout_content)
        self.assertIn("run-doc", stdout_content)

    def test_help_argument(self):
        """Test that --help shows help and exits."""
        sys.argv = ["yggdrasil", "--help"]

        with self.assertRaises(SystemExit) as context:
            with patch("sys.stdout", new_callable=StringIO):
                main()

        # argparse exits with code 0 for help
        self.assertEqual(context.exception.code, 0)

    def test_daemon_mode_arguments(self):
        """Test daemon mode argument parsing."""
        sys.argv = ["yggdrasil", "daemon"]

        with (
            patch("yggdrasil.cli.ConfigLoader") as mock_config_loader,
            patch("yggdrasil.cli.YggdrasilCore") as mock_core_class,
            patch("asyncio.run") as mock_asyncio_run,
        ):

            mock_config_loader.return_value.load_config.return_value = self.mock_config
            mock_core = Mock()
            mock_core_class.return_value = mock_core

            main()

            # Verify daemon mode was processed correctly
            mock_core.setup_handlers.assert_called_once()
            mock_core.setup_watchers.assert_called_once()
            mock_asyncio_run.assert_called_once_with(mock_core.start())

    def test_daemon_mode_with_dev_flag(self):
        """Test daemon mode with development flag."""
        sys.argv = ["yggdrasil", "--dev", "daemon"]

        with (
            patch("yggdrasil.cli.ConfigLoader") as mock_config_loader,
            patch("yggdrasil.cli.YggdrasilCore") as mock_core_class,
            patch("yggdrasil.cli.YggSession") as mock_session,
            patch("asyncio.run"),
        ):

            mock_config_loader.return_value.load_config.return_value = self.mock_config
            mock_core_class.return_value = Mock()

            main()

            # Verify dev mode was set
            mock_session.init_dev_mode.assert_called_once_with(True)

    def test_run_doc_mode_arguments(self):
        """Test run-doc mode argument parsing."""
        sys.argv = ["yggdrasil", "run-doc", "test_doc_id"]

        with (
            patch("yggdrasil.cli.ConfigLoader") as mock_config_loader,
            patch("yggdrasil.cli.YggdrasilCore") as mock_core_class,
            patch("yggdrasil.cli.YggSession") as mock_session,
        ):

            mock_config_loader.return_value.load_config.return_value = self.mock_config
            mock_core = Mock()
            mock_core_class.return_value = mock_core

            main()

            # Verify run-doc mode was processed correctly
            mock_core.setup_handlers.assert_called_once()
            mock_core.run_once.assert_called_once_with(doc_id="test_doc_id")
            mock_session.init_manual_submit.assert_called_once_with(False)

    def test_run_doc_mode_with_manual_submit(self):
        """Test run-doc mode with manual submit flag."""
        sys.argv = ["yggdrasil", "run-doc", "test_doc_id", "--manual-submit"]

        with (
            patch("yggdrasil.cli.ConfigLoader") as mock_config_loader,
            patch("yggdrasil.cli.YggdrasilCore") as mock_core_class,
            patch("yggdrasil.cli.YggSession") as mock_session,
        ):

            mock_config_loader.return_value.load_config.return_value = self.mock_config
            mock_core = Mock()
            mock_core_class.return_value = mock_core

            main()

            # Verify manual submit was set to True
            mock_session.init_manual_submit.assert_called_once_with(True)
            mock_core.run_once.assert_called_once_with(doc_id="test_doc_id")

    def test_run_doc_mode_short_manual_submit_flag(self):
        """Test run-doc mode with short -m flag."""
        sys.argv = ["yggdrasil", "run-doc", "test_doc_id", "-m"]

        with (
            patch("yggdrasil.cli.ConfigLoader") as mock_config_loader,
            patch("yggdrasil.cli.YggdrasilCore") as mock_core_class,
            patch("yggdrasil.cli.YggSession") as mock_session,
        ):

            mock_config_loader.return_value.load_config.return_value = self.mock_config
            mock_core = Mock()
            mock_core_class.return_value = mock_core

            main()

            # Verify manual submit was set to True
            mock_session.init_manual_submit.assert_called_once_with(True)

    def test_run_doc_missing_doc_id(self):
        """Test run-doc mode without document ID."""
        sys.argv = ["yggdrasil", "run-doc"]

        with self.assertRaises(SystemExit) as context:
            with patch("sys.stderr", new_callable=StringIO):
                main()

        # argparse should exit with error code for missing argument
        self.assertEqual(context.exception.code, 2)

    def test_invalid_mode(self):
        """Test invalid mode argument."""
        sys.argv = ["yggdrasil", "invalid_mode"]

        with self.assertRaises(SystemExit) as context:
            with patch("sys.stderr", new_callable=StringIO):
                main()

        # argparse should exit with error code for invalid choice
        self.assertEqual(context.exception.code, 2)

    def test_silent_flag_logging_configuration(self):
        """Test that --silent flag configures logging correctly."""
        sys.argv = ["yggdrasil", "--silent", "daemon"]

        with (
            patch("yggdrasil.cli.configure_logging") as mock_configure_logging,
            patch("yggdrasil.cli.ConfigLoader") as mock_config_loader,
            patch("yggdrasil.cli.YggdrasilCore") as mock_core_class,
            patch("asyncio.run"),
        ):
            mock_config_loader.return_value.load_config.return_value = self.mock_config
            mock_core_class.return_value = Mock()

            main()

            # Verify configure_logging was called with console=False for silent mode
            mock_configure_logging.assert_called_once_with(debug=False, console=False)

    def test_dev_flag_logging_configuration(self):
        """Test that --dev flag configures logging correctly."""
        sys.argv = ["yggdrasil", "--dev", "daemon"]

        with (
            patch("yggdrasil.cli.configure_logging") as mock_configure_logging,
            patch("yggdrasil.cli.ConfigLoader") as mock_config_loader,
            patch("yggdrasil.cli.YggdrasilCore") as mock_core_class,
            patch("asyncio.run"),
        ):
            mock_config_loader.return_value.load_config.return_value = self.mock_config
            mock_core_class.return_value = Mock()

            main()

            # Verify configure_logging was called with debug=True, console=True for dev mode
            mock_configure_logging.assert_called_once_with(debug=True, console=True)

    def test_normal_mode_logging_configuration(self):
        """Test that normal mode (no flags) configures logging correctly."""
        sys.argv = ["yggdrasil", "daemon"]

        with (
            patch("yggdrasil.cli.configure_logging") as mock_configure_logging,
            patch("yggdrasil.cli.ConfigLoader") as mock_config_loader,
            patch("yggdrasil.cli.YggdrasilCore") as mock_core_class,
            patch("asyncio.run"),
        ):
            mock_config_loader.return_value.load_config.return_value = self.mock_config
            mock_core_class.return_value = Mock()

            main()

            # Verify configure_logging was called with debug=False, console=True for normal mode
            mock_configure_logging.assert_called_once_with(debug=False, console=True)

    # =====================================================
    # CONFIGURATION AND INITIALIZATION TESTS
    # =====================================================

    def test_config_loading(self):
        """Test configuration loading process."""
        sys.argv = ["yggdrasil", "daemon"]

        with (
            patch("yggdrasil.cli.ConfigLoader") as mock_config_loader,
            patch("yggdrasil.cli.YggdrasilCore") as mock_core_class,
            patch("asyncio.run"),
        ):

            mock_config_loader_instance = Mock()
            mock_config_loader.return_value = mock_config_loader_instance
            mock_config_loader_instance.load_config.return_value = self.mock_config
            mock_core_class.return_value = Mock()

            main()

            # Verify config loading
            mock_config_loader.assert_called_once()
            mock_config_loader_instance.load_config.assert_called_once_with(
                "config.json"
            )
            mock_core_class.assert_called_once_with(self.mock_config)

    def test_yggdrasil_core_initialization(self):
        """Test YggdrasilCore initialization."""
        sys.argv = ["yggdrasil", "daemon"]

        with (
            patch("yggdrasil.cli.ConfigLoader") as mock_config_loader,
            patch("yggdrasil.cli.YggdrasilCore") as mock_core_class,
            patch("asyncio.run"),
        ):

            mock_config_loader.return_value.load_config.return_value = self.mock_config
            mock_core = Mock()
            mock_core_class.return_value = mock_core

            main()

            # Verify core initialization and setup
            mock_core_class.assert_called_once_with(self.mock_config)
            mock_core.setup_handlers.assert_called_once()

    def test_session_initialization_order(self):
        """Test that YggSession is initialized before core setup."""
        sys.argv = ["yggdrasil", "--dev", "run-doc", "test_doc", "--manual-submit"]

        with (
            patch("yggdrasil.cli.ConfigLoader") as mock_config_loader,
            patch("yggdrasil.cli.YggdrasilCore") as mock_core_class,
            patch("yggdrasil.cli.YggSession") as mock_session,
        ):

            mock_config_loader.return_value.load_config.return_value = self.mock_config
            mock_core_class.return_value = Mock()

            main()

            # Verify session is initialized before core operations
            expected_calls = [call.init_dev_mode(True), call.init_manual_submit(True)]
            mock_session.assert_has_calls(expected_calls)

    # =====================================================
    # DAEMON MODE TESTS
    # =====================================================

    def test_daemon_mode_full_flow(self):
        """Test complete daemon mode execution flow."""
        sys.argv = ["yggdrasil", "daemon"]

        with (
            patch("yggdrasil.cli.ConfigLoader") as mock_config_loader,
            patch("yggdrasil.cli.YggdrasilCore") as mock_core_class,
            patch("asyncio.run") as mock_asyncio_run,
        ):

            mock_config_loader.return_value.load_config.return_value = self.mock_config
            mock_core = Mock()
            mock_core_class.return_value = mock_core

            main()

            # Verify complete daemon setup flow
            mock_core.setup_handlers.assert_called_once()
            mock_core.setup_watchers.assert_called_once()
            mock_asyncio_run.assert_called_once_with(mock_core.start())

    def test_daemon_mode_keyboard_interrupt(self):
        """Test daemon mode handling of KeyboardInterrupt."""
        sys.argv = ["yggdrasil", "daemon"]

        with (
            patch("yggdrasil.cli.ConfigLoader") as mock_config_loader,
            patch("yggdrasil.cli.YggdrasilCore") as mock_core_class,
            patch("asyncio.run") as mock_asyncio_run,
        ):

            mock_config_loader.return_value.load_config.return_value = self.mock_config
            mock_core = Mock()
            mock_core_class.return_value = mock_core

            # First call (start) raises KeyboardInterrupt, second call (stop) succeeds
            mock_asyncio_run.side_effect = [KeyboardInterrupt(), None]

            main()

            # Verify both start and stop were called
            expected_calls = [call(mock_core.start()), call(mock_core.stop())]
            mock_asyncio_run.assert_has_calls(expected_calls)

    # =====================================================
    # RUN-DOC MODE TESTS
    # =====================================================

    def test_run_doc_mode_full_flow(self):
        """Test complete run-doc mode execution flow."""
        sys.argv = ["yggdrasil", "run-doc", "test_document_id"]

        with (
            patch("yggdrasil.cli.ConfigLoader") as mock_config_loader,
            patch("yggdrasil.cli.YggdrasilCore") as mock_core_class,
            patch("yggdrasil.cli.YggSession") as mock_session,
        ):

            mock_config_loader.return_value.load_config.return_value = self.mock_config
            mock_core = Mock()
            mock_core_class.return_value = mock_core

            main()

            # Verify complete run-doc flow
            mock_session.init_manual_submit.assert_called_once_with(False)
            mock_core.setup_handlers.assert_called_once()
            mock_core.run_once.assert_called_once_with(doc_id="test_document_id")

            # Verify watchers are NOT set up in run-doc mode
            mock_core.setup_watchers.assert_not_called()

    def test_run_doc_with_special_characters_in_doc_id(self):
        """Test run-doc mode with special characters in document ID."""
        special_doc_id = "test-doc_id.123@domain"
        sys.argv = ["yggdrasil", "run-doc", special_doc_id]

        with (
            patch("yggdrasil.cli.ConfigLoader") as mock_config_loader,
            patch("yggdrasil.cli.YggdrasilCore") as mock_core_class,
            patch("yggdrasil.cli.YggSession"),
        ):

            mock_config_loader.return_value.load_config.return_value = self.mock_config
            mock_core = Mock()
            mock_core_class.return_value = mock_core

            main()

            # Verify special characters are passed correctly
            mock_core.run_once.assert_called_once_with(doc_id=special_doc_id)

    # =====================================================
    # ERROR HANDLING TESTS
    # =====================================================

    def test_config_loading_error(self):
        """Test error handling when config loading fails."""
        sys.argv = ["yggdrasil", "daemon"]

        with patch("yggdrasil.cli.ConfigLoader") as mock_config_loader:
            mock_config_loader.return_value.load_config.side_effect = Exception(
                "Config load failed"
            )

            with self.assertRaises(Exception) as context:
                main()

            self.assertIn("Config load failed", str(context.exception))

    def test_yggdrasil_core_initialization_error(self):
        """Test error handling when YggdrasilCore initialization fails."""
        sys.argv = ["yggdrasil", "daemon"]

        with (
            patch("yggdrasil.cli.ConfigLoader") as mock_config_loader,
            patch("yggdrasil.cli.YggdrasilCore") as mock_core_class,
        ):

            mock_config_loader.return_value.load_config.return_value = self.mock_config
            mock_core_class.side_effect = Exception("Core init failed")

            with self.assertRaises(Exception) as context:
                main()

            self.assertIn("Core init failed", str(context.exception))

    def test_session_already_set_error(self):
        """Test error handling when YggSession is already set."""
        sys.argv = ["yggdrasil", "--dev", "daemon"]

        with (
            patch("yggdrasil.cli.ConfigLoader") as mock_config_loader,
            patch("yggdrasil.cli.YggdrasilCore") as mock_core_class,
            patch("yggdrasil.cli.YggSession") as mock_session,
        ):

            mock_config_loader.return_value.load_config.return_value = self.mock_config
            mock_core_class.return_value = Mock()
            mock_session.init_dev_mode.side_effect = RuntimeError(
                "Dev mode already set"
            )

            with self.assertRaises(RuntimeError) as context:
                main()

            self.assertIn("Dev mode already set", str(context.exception))

    def test_asyncio_error_in_daemon_mode(self):
        """Test error handling when asyncio operations fail in daemon mode."""
        sys.argv = ["yggdrasil", "daemon"]

        with (
            patch("yggdrasil.cli.ConfigLoader") as mock_config_loader,
            patch("yggdrasil.cli.YggdrasilCore") as mock_core_class,
            patch("asyncio.run") as mock_asyncio_run,
        ):

            mock_config_loader.return_value.load_config.return_value = self.mock_config
            mock_core_class.return_value = Mock()
            mock_asyncio_run.side_effect = Exception("Asyncio error")

            with self.assertRaises(Exception) as context:
                main()

            self.assertIn("Asyncio error", str(context.exception))

    # =====================================================
    # LOGGING AND DEBUG TESTS
    # =====================================================

    def test_logging_configuration(self):
        """Test that logging configuration happens correctly during main() execution."""
        sys.argv = ["yggdrasil", "daemon"]

        with (
            patch("yggdrasil.cli.configure_logging") as mock_configure_logging,
            patch("yggdrasil.cli.custom_logger") as mock_custom_logger,
            patch("yggdrasil.cli.ConfigLoader") as mock_config_loader,
            patch("yggdrasil.cli.YggdrasilCore") as mock_core_class,
            patch("asyncio.run"),
        ):
            mock_config_loader.return_value.load_config.return_value = self.mock_config
            mock_core_class.return_value = Mock()
            mock_logger = Mock()
            mock_custom_logger.return_value = mock_logger

            main()

            # Verify that logging was configured and logger was created
            mock_configure_logging.assert_called_once_with(debug=False, console=True)
            mock_custom_logger.assert_called_once_with("Yggdrasil")
            # Verify that debug logging was called (indicates logging is working)
            mock_logger.debug.assert_called_once_with("Yggdrasil: Starting up...")

    def test_dev_mode_affects_session_only(self):
        """Test that --dev flag only affects YggSession, not other components directly."""
        sys.argv = ["yggdrasil", "--dev", "daemon"]

        with (
            patch("yggdrasil.cli.ConfigLoader") as mock_config_loader,
            patch("yggdrasil.cli.YggdrasilCore") as mock_core_class,
            patch("yggdrasil.cli.YggSession") as mock_session,
            patch("asyncio.run"),
        ):

            mock_config_loader.return_value.load_config.return_value = self.mock_config
            mock_core_class.return_value = Mock()

            main()

            # Verify only the session is affected by dev mode
            mock_session.init_dev_mode.assert_called_once_with(True)
            # ConfigLoader and YggdrasilCore should be called the same way regardless
            mock_config_loader.return_value.load_config.assert_called_once_with(
                "config.json"
            )

    # =====================================================
    # INTEGRATION AND EDGE CASE TESTS
    # =====================================================

    def test_all_components_integration(self):
        """Test integration between all CLI components."""
        sys.argv = ["yggdrasil", "--dev", "run-doc", "integration_test_doc", "-m"]

        with (
            patch("yggdrasil.cli.ConfigLoader") as mock_config_loader,
            patch("yggdrasil.cli.YggdrasilCore") as mock_core_class,
            patch("yggdrasil.cli.YggSession") as mock_session,
        ):

            mock_config_loader.return_value.load_config.return_value = self.mock_config
            mock_core = Mock()
            mock_core_class.return_value = mock_core

            main()

            # Verify complete integration flow
            mock_session.init_dev_mode.assert_called_once_with(True)
            mock_config_loader.return_value.load_config.assert_called_once_with(
                "config.json"
            )
            mock_core_class.assert_called_once_with(self.mock_config)
            mock_core.setup_handlers.assert_called_once()
            mock_session.init_manual_submit.assert_called_once_with(True)
            mock_core.run_once.assert_called_once_with(doc_id="integration_test_doc")

    def test_minimal_daemon_invocation(self):
        """Test minimal daemon mode invocation."""
        sys.argv = ["yggdrasil", "daemon"]

        with (
            patch("yggdrasil.cli.ConfigLoader") as mock_config_loader,
            patch("yggdrasil.cli.YggdrasilCore") as mock_core_class,
            patch("yggdrasil.cli.YggSession") as mock_session,
            patch("asyncio.run"),
        ):

            mock_config_loader.return_value.load_config.return_value = self.mock_config
            mock_core_class.return_value = Mock()

            main()

            # Verify minimal setup works
            mock_session.init_dev_mode.assert_called_once_with(
                False
            )  # Default dev=False

    def test_minimal_run_doc_invocation(self):
        """Test minimal run-doc mode invocation."""
        sys.argv = ["yggdrasil", "run-doc", "minimal_doc"]

        with (
            patch("yggdrasil.cli.ConfigLoader") as mock_config_loader,
            patch("yggdrasil.cli.YggdrasilCore") as mock_core_class,
            patch("yggdrasil.cli.YggSession") as mock_session,
        ):

            mock_config_loader.return_value.load_config.return_value = self.mock_config
            mock_core_class.return_value = Mock()

            main()

            # Verify minimal setup works
            mock_session.init_dev_mode.assert_called_once_with(False)
            mock_session.init_manual_submit.assert_called_once_with(False)

    def test_command_line_order_independence(self):
        """Test that global flags must come before subcommands (argparse behavior)."""
        # Test that --dev must come before the subcommand (this is argparse's expected behavior)
        valid_order = ["yggdrasil", "--dev", "run-doc", "test_doc", "--manual-submit"]
        invalid_orders = [
            ["yggdrasil", "run-doc", "--dev", "test_doc", "--manual-submit"],
            ["yggdrasil", "run-doc", "test_doc", "--dev", "--manual-submit"],
            ["yggdrasil", "run-doc", "test_doc", "--manual-submit", "--dev"],
        ]

        # Test valid order works
        sys.argv = valid_order
        with (
            patch("yggdrasil.cli.ConfigLoader") as mock_config_loader,
            patch("yggdrasil.cli.YggdrasilCore") as mock_core_class,
            patch("yggdrasil.cli.YggSession") as mock_session,
        ):

            mock_config_loader.return_value.load_config.return_value = self.mock_config
            mock_core_class.return_value = Mock()

            main()

            # Verify the valid order works
            mock_session.init_dev_mode.assert_called_with(True)
            mock_session.init_manual_submit.assert_called_with(True)

        # Test that invalid orders fail (this is expected argparse behavior)
        for argv in invalid_orders:
            with self.subTest(argv=argv):
                sys.argv = argv

                with self.assertRaises(SystemExit) as context:
                    with patch("sys.stderr", new_callable=StringIO):
                        main()

                # argparse should exit with error code 2 for invalid argument order
                self.assertEqual(context.exception.code, 2)

                # Reset for next iteration
                self.setUp()

    # =====================================================
    # ARGUMENT VALIDATION TESTS
    # =====================================================

    def test_empty_doc_id(self):
        """Test run-doc mode with empty document ID."""
        sys.argv = ["yggdrasil", "run-doc", ""]

        with (
            patch("yggdrasil.cli.ConfigLoader") as mock_config_loader,
            patch("yggdrasil.cli.YggdrasilCore") as mock_core_class,
            patch("yggdrasil.cli.YggSession"),
        ):

            mock_config_loader.return_value.load_config.return_value = self.mock_config
            mock_core = Mock()
            mock_core_class.return_value = mock_core

            main()

            # Even empty string should be passed through
            mock_core.run_once.assert_called_once_with(doc_id="")

    def test_very_long_doc_id(self):
        """Test run-doc mode with very long document ID."""
        long_doc_id = "a" * 1000  # Very long document ID
        sys.argv = ["yggdrasil", "run-doc", long_doc_id]

        with (
            patch("yggdrasil.cli.ConfigLoader") as mock_config_loader,
            patch("yggdrasil.cli.YggdrasilCore") as mock_core_class,
            patch("yggdrasil.cli.YggSession"),
        ):

            mock_config_loader.return_value.load_config.return_value = self.mock_config
            mock_core = Mock()
            mock_core_class.return_value = mock_core

            main()

            # Long document ID should be handled
            mock_core.run_once.assert_called_once_with(doc_id=long_doc_id)

    def test_daemon_mode_with_manual_submit_error(self):
        """Test daemon mode doesn't have manual_submit attribute (defensive code coverage)."""
        # Note: The manual_submit check in daemon mode (line 70) is defensive code that
        # cannot be reached in practice because argparse only defines --manual-submit
        # for the run-doc subcommand. The getattr(args, "manual_submit", False) will
        # always return False for daemon mode since the attribute doesn't exist.
        # This test verifies the normal daemon behavior (no manual_submit attribute).

        sys.argv = ["yggdrasil", "daemon"]

        with (
            patch("yggdrasil.cli.ConfigLoader") as mock_config_loader,
            patch("yggdrasil.cli.YggdrasilCore") as mock_core_class,
            patch("asyncio.run"),
        ):

            mock_config_loader.return_value.load_config.return_value = self.mock_config
            mock_core = Mock()
            mock_core_class.return_value = mock_core

            main()

            # Verify daemon mode works normally (defensive check doesn't trigger)
            mock_core.setup_handlers.assert_called_once()
            mock_core.setup_watchers.assert_called_once()

    def test_main_module_execution(self):
        """Test that main can be imported and called (covers entry point functionality)."""
        # Note: The if __name__ == '__main__' guard (line 90) is only executed when
        # running the script directly, not during import or exec. This test verifies
        # that the main function works correctly when called directly, which is the
        # same code path that would be triggered by the __main__ guard.

        sys.argv = ["yggdrasil", "daemon"]

        with (
            patch("yggdrasil.cli.ConfigLoader") as mock_config_loader,
            patch("yggdrasil.cli.YggdrasilCore") as mock_core_class,
            patch("asyncio.run"),
        ):

            mock_config_loader.return_value.load_config.return_value = self.mock_config
            mock_core_class.return_value = Mock()

            # Call main() directly to verify it works (same as __main__ guard would do)
            main()

            # Verify main() executed correctly
            mock_config_loader.assert_called_once()
            mock_core_class.assert_called_once()


if __name__ == "__main__":
    unittest.main()

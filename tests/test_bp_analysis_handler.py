import asyncio
import unittest
from unittest.mock import AsyncMock, Mock, call, patch

from lib.handlers.bp_analysis_handler import BestPracticeAnalysisHandler


class TestBestPracticeAnalysisHandler(unittest.TestCase):
    """
    Comprehensive tests for BestPracticeAnalysisHandler - the ProjectDB change event handler.

    Tests the handler's ability to process ProjectDB document changes by loading
    and executing appropriate best-practice realms, including payload validation,
    realm resolution, execution patterns, and error handling.
    """

    def setUp(self):
        """Set up test fixtures for each test."""
        # Mock dependencies to isolate handler testing
        self.mock_ydm_patcher = patch(
            "lib.handlers.bp_analysis_handler.YggdrasilDBManager"
        )
        self.mock_ygg_patcher = patch("lib.handlers.bp_analysis_handler.Ygg")
        self.mock_logger_patcher = patch(
            "lib.handlers.bp_analysis_handler.logging.getLogger"
        )

        self.mock_ydm_class = self.mock_ydm_patcher.start()
        self.mock_ygg = self.mock_ygg_patcher.start()
        self.mock_logger_factory = self.mock_logger_patcher.start()

        # Create mock instances
        self.mock_ydm_instance = Mock()
        self.mock_ydm_class.return_value = self.mock_ydm_instance

        self.mock_logger = Mock()
        self.mock_logger_factory.return_value = self.mock_logger

        # Create handler instance
        self.handler = BestPracticeAnalysisHandler()

        # Test payloads
        self.valid_payload = {
            "document": {
                "project_id": "test_project_123",
                "type": "project",
                "auto_submit": True,
                "data": {"key": "value"},
            },
            "module_location": "lib.realms.test_realm",
        }

        self.minimal_payload = {
            "document": {"project_id": "minimal_project"},
            "module_location": "lib.realms.minimal_realm",
        }

    def tearDown(self):
        """Clean up after each test."""
        self.mock_ydm_patcher.stop()
        self.mock_ygg_patcher.stop()
        self.mock_logger_patcher.stop()

    # =====================================================
    # INITIALIZATION TESTS
    # =====================================================

    def test_initialization(self):
        """Test handler initialization."""
        # YggdrasilDBManager should be instantiated
        self.mock_ydm_class.assert_called_once()
        self.assertEqual(self.handler.ydm, self.mock_ydm_instance)

        # Logger should be created with correct name
        self.mock_logger_factory.assert_called_once_with("BPA-Handler")
        self.assertEqual(self.handler.logger, self.mock_logger)

    def test_inheritance_from_base_handler(self):
        """Test that handler properly inherits from BaseHandler."""
        from lib.handlers.base_handler import BaseHandler

        self.assertIsInstance(self.handler, BaseHandler)

        # Should have all required methods
        self.assertTrue(hasattr(self.handler, "handle_task"))
        self.assertTrue(hasattr(self.handler, "__call__"))
        self.assertTrue(hasattr(self.handler, "run_now"))

        # handle_task should be async
        self.assertTrue(asyncio.iscoroutinefunction(self.handler.handle_task))

    # =====================================================
    # PAYLOAD VALIDATION TESTS
    # =====================================================

    def test_handle_task_missing_document(self):
        """Test handle_task with missing document in payload."""

        async def test_missing_doc():
            payload = {"module_location": "lib.realms.test_realm"}

            await self.handler.handle_task(payload)

            # Should log warning and return early
            self.mock_logger.warning.assert_called_once_with(
                "handle_async: missing or invalid 'document' in payload"
            )

            # Should not attempt to load realm
            self.mock_ygg.load_realm_class.assert_not_called()

        asyncio.run(test_missing_doc())

    def test_handle_task_invalid_document_type(self):
        """Test handle_task with invalid document type."""

        async def test_invalid_doc():
            payload = {
                "document": "not_a_dict",  # Invalid type
                "module_location": "lib.realms.test_realm",
            }

            await self.handler.handle_task(payload)

            # Should log warning and return early
            self.mock_logger.warning.assert_called_once_with(
                "handle_async: missing or invalid 'document' in payload"
            )

            # Should not attempt to load realm
            self.mock_ygg.load_realm_class.assert_not_called()

        asyncio.run(test_invalid_doc())

    def test_handle_task_missing_module_location(self):
        """Test handle_task with missing module_location in payload."""

        async def test_missing_module():
            payload = {"document": {"project_id": "test_project"}}

            await self.handler.handle_task(payload)

            # Should log warning and return early
            self.mock_logger.warning.assert_called_once_with(
                "handle_async: missing or invalid 'module_location' in payload"
            )

            # Should not attempt to load realm
            self.mock_ygg.load_realm_class.assert_not_called()

        asyncio.run(test_missing_module())

    def test_handle_task_invalid_module_location_type(self):
        """Test handle_task with invalid module_location type."""

        async def test_invalid_module():
            payload = {
                "document": {"project_id": "test_project"},
                "module_location": 123,  # Invalid type
            }

            await self.handler.handle_task(payload)

            # Should log warning and return early
            self.mock_logger.warning.assert_called_once_with(
                "handle_async: missing or invalid 'module_location' in payload"
            )

            # Should not attempt to load realm
            self.mock_ygg.load_realm_class.assert_not_called()

        asyncio.run(test_invalid_module())

    # =====================================================
    # REALM LOADING TESTS
    # =====================================================

    def test_handle_task_realm_loading_success(self):
        """Test successful realm loading and execution."""

        async def test_realm_success():
            # Mock successful realm loading
            mock_realm_class = Mock()
            mock_realm_instance = Mock()
            mock_realm_instance.proceed = True
            mock_realm_instance.launch_template = AsyncMock()
            mock_realm_class.return_value = mock_realm_instance
            self.mock_ygg.load_realm_class.return_value = mock_realm_class

            await self.handler.handle_task(self.valid_payload)

            # Should attempt to load realm
            self.mock_ygg.load_realm_class.assert_called_once_with(
                "lib.realms.test_realm"
            )

            # Should instantiate realm with document and ydm
            mock_realm_class.assert_called_once_with(
                self.valid_payload["document"], self.mock_ydm_instance
            )

            # Should call launch_template
            mock_realm_instance.launch_template.assert_called_once()

            # Should log progress
            expected_calls = [
                call(
                    "Processing ProjectDB change for project %s → module %s",
                    "test_project_123",
                    "lib.realms.test_realm",
                ),
                call("Launching realm for project %s", "test_project_123"),
                call("Realm completed for project %s", "test_project_123"),
            ]
            self.mock_logger.info.assert_has_calls(expected_calls)

        asyncio.run(test_realm_success())

    def test_handle_task_realm_loading_failure(self):
        """Test realm loading failure."""

        async def test_realm_failure():
            # Mock failed realm loading
            self.mock_ygg.load_realm_class.return_value = None

            await self.handler.handle_task(self.valid_payload)

            # Should attempt to load realm
            self.mock_ygg.load_realm_class.assert_called_once_with(
                "lib.realms.test_realm"
            )

            # Should log error
            self.mock_logger.error.assert_called_once_with(
                "Cannot load realm class '%s' for project %s",
                "lib.realms.test_realm",
                "test_project_123",
            )

        asyncio.run(test_realm_failure())

    def test_handle_task_realm_proceed_false(self):
        """Test realm with proceed=False."""

        async def test_realm_no_proceed():
            # Mock realm that shouldn't proceed
            mock_realm_class = Mock()
            mock_realm_instance = Mock()
            mock_realm_instance.proceed = False
            mock_realm_instance.launch_template = (
                AsyncMock()
            )  # Available but shouldn't be called
            mock_realm_class.return_value = mock_realm_instance
            self.mock_ygg.load_realm_class.return_value = mock_realm_class

            await self.handler.handle_task(self.valid_payload)

            # Should create realm instance
            mock_realm_class.assert_called_once()

            # Should not call launch_template due to proceed=False
            mock_realm_instance.launch_template.assert_not_called()

            # Should log skip message
            self.mock_logger.info.assert_any_call(
                "Realm skipped (proceed=False) for project %s", "test_project_123"
            )

        asyncio.run(test_realm_no_proceed())

    def test_handle_task_realm_launch_exception(self):
        """Test exception during realm launch."""

        async def test_realm_exception():
            # Mock realm that raises exception
            mock_realm_class = Mock()
            mock_realm_instance = Mock()
            mock_realm_instance.proceed = True
            mock_realm_instance.launch_template = AsyncMock(
                side_effect=ValueError("Test error")
            )
            mock_realm_class.return_value = mock_realm_instance
            self.mock_ygg.load_realm_class.return_value = mock_realm_class

            await self.handler.handle_task(self.valid_payload)

            # Should still call launch_template
            mock_realm_instance.launch_template.assert_called_once()

            # Should log error with exception info
            self.mock_logger.error.assert_called_once_with(
                "Error running realm for project %s", "test_project_123", exc_info=True
            )

        asyncio.run(test_realm_exception())

    # =====================================================
    # PROJECT ID HANDLING TESTS
    # =====================================================

    def test_handle_task_missing_project_id(self):
        """Test handling when project_id is missing from document."""

        async def test_missing_project_id():
            payload = {
                "document": {"type": "project"},  # No project_id
                "module_location": "lib.realms.test_realm",
            }

            mock_realm_class = Mock()
            mock_realm_instance = Mock()
            mock_realm_instance.proceed = True
            mock_realm_instance.launch_template = AsyncMock()
            mock_realm_class.return_value = mock_realm_instance
            self.mock_ygg.load_realm_class.return_value = mock_realm_class

            await self.handler.handle_task(payload)

            # Should use default project_id
            expected_calls = [
                call(
                    "Processing ProjectDB change for project %s → module %s",
                    "<unknown>",
                    "lib.realms.test_realm",
                ),
                call("Launching realm for project %s", "<unknown>"),
                call("Realm completed for project %s", "<unknown>"),
            ]
            self.mock_logger.info.assert_has_calls(expected_calls)

        asyncio.run(test_missing_project_id())

    def test_handle_task_empty_project_id(self):
        """Test handling when project_id is empty."""

        async def test_empty_project_id():
            payload = {
                "document": {"project_id": ""},
                "module_location": "lib.realms.test_realm",
            }

            mock_realm_class = Mock()
            mock_realm_instance = Mock()
            mock_realm_instance.proceed = True
            mock_realm_instance.launch_template = AsyncMock()
            mock_realm_class.return_value = mock_realm_instance
            self.mock_ygg.load_realm_class.return_value = mock_realm_class

            await self.handler.handle_task(payload)

            # Should use empty string as project_id
            self.mock_logger.info.assert_any_call(
                "Processing ProjectDB change for project %s → module %s",
                "",
                "lib.realms.test_realm",
            )

        asyncio.run(test_empty_project_id())

    # =====================================================
    # CALL METHOD TESTS (ASYNC SCHEDULING)
    # =====================================================

    def test_call_method_creates_task(self):
        """Test that __call__ creates async task."""
        with patch("asyncio.create_task") as mock_create_task:
            self.handler(self.valid_payload)

            # Should create task with handle_task
            mock_create_task.assert_called_once()

            # Verify the task is for handle_task
            task_arg = mock_create_task.call_args[0][0]
            self.assertTrue(asyncio.iscoroutine(task_arg))

    def test_call_method_runtime_error_fallback(self):
        """Test fallback behavior when create_task raises RuntimeError."""
        with patch(
            "asyncio.create_task", side_effect=RuntimeError("No running loop")
        ) as mock_create_task:
            with patch("asyncio.get_event_loop") as mock_get_loop:
                mock_loop = Mock()
                mock_get_loop.return_value = mock_loop

                self.handler(self.valid_payload)

                # Should try create_task first
                mock_create_task.assert_called_once()

                # Should fallback to get_event_loop
                mock_get_loop.assert_called_once()
                mock_loop.create_task.assert_called_once()

    # =====================================================
    # RUN_NOW METHOD TESTS (INHERITED)
    # =====================================================

    def test_run_now_method_inherited(self):
        """Test that run_now method is properly inherited from BaseHandler."""
        # Should have run_now method from base class
        self.assertTrue(hasattr(self.handler, "run_now"))
        self.assertTrue(callable(self.handler.run_now))

        # Should not be a coroutine function
        self.assertFalse(asyncio.iscoroutinefunction(self.handler.run_now))

    def test_run_now_executes_handle_task(self):
        """Test that run_now properly executes handle_task."""
        # Mock a successful realm execution
        mock_realm_class = Mock()
        mock_realm_instance = Mock()
        mock_realm_instance.proceed = True
        mock_realm_instance.launch_template = AsyncMock()
        mock_realm_class.return_value = mock_realm_instance
        self.mock_ygg.load_realm_class.return_value = mock_realm_class

        # Call run_now
        self.handler.run_now(self.valid_payload)

        # Should have executed the realm
        self.mock_ygg.load_realm_class.assert_called_once_with("lib.realms.test_realm")
        mock_realm_instance.launch_template.assert_called_once()

    # =====================================================
    # INTEGRATION SCENARIO TESTS
    # =====================================================

    def test_projectdb_change_scenario(self):
        """Test complete ProjectDB change scenario."""

        async def test_complete_scenario():
            # Simulate a real ProjectDB change event
            payload = {
                "document": {
                    "project_id": "P001234",
                    "project_name": "Test Project",
                    "type": "project",
                    "auto_submit": True,
                    "application": "test_app",
                    "priority": "high",
                },
                "module_location": "lib.realms.genomics.test_realm",
            }

            # Mock successful realm execution
            mock_realm_class = Mock()
            mock_realm_instance = Mock()
            mock_realm_instance.proceed = True
            mock_realm_instance.launch_template = AsyncMock()
            mock_realm_class.return_value = mock_realm_instance
            self.mock_ygg.load_realm_class.return_value = mock_realm_class

            await self.handler.handle_task(payload)

            # Verify complete workflow
            self.mock_ygg.load_realm_class.assert_called_once_with(
                "lib.realms.genomics.test_realm"
            )
            mock_realm_class.assert_called_once_with(
                payload["document"], self.mock_ydm_instance
            )
            mock_realm_instance.launch_template.assert_called_once()

            # Check logging
            self.mock_logger.info.assert_any_call(
                "Processing ProjectDB change for project %s → module %s",
                "P001234",
                "lib.realms.genomics.test_realm",
            )

        asyncio.run(test_complete_scenario())

    def test_cli_one_off_execution(self):
        """Test CLI one-off execution pattern."""
        # Mock successful realm
        mock_realm_class = Mock()
        mock_realm_instance = Mock()
        mock_realm_instance.proceed = True
        mock_realm_instance.launch_template = AsyncMock()
        mock_realm_class.return_value = mock_realm_instance
        self.mock_ygg.load_realm_class.return_value = mock_realm_class

        # Execute via run_now (CLI pattern)
        self.handler.run_now(self.valid_payload)

        # Should complete synchronously
        mock_realm_instance.launch_template.assert_called_once()
        self.mock_logger.info.assert_any_call(
            "Realm completed for project %s", "test_project_123"
        )

    def test_daemon_async_execution(self):
        """Test daemon async execution pattern."""

        async def test_daemon_execution():
            # Mock successful realm
            mock_realm_class = Mock()
            mock_realm_instance = Mock()
            mock_realm_instance.proceed = True
            mock_realm_instance.launch_template = AsyncMock()
            mock_realm_class.return_value = mock_realm_instance
            self.mock_ygg.load_realm_class.return_value = mock_realm_class

            # Create task (daemon pattern)
            task = asyncio.create_task(self.handler.handle_task(self.valid_payload))
            await task

            # Should complete asynchronously
            mock_realm_instance.launch_template.assert_called_once()

        asyncio.run(test_daemon_execution())

    # =====================================================
    # ERROR HANDLING AND EDGE CASES
    # =====================================================

    def test_complex_payload_handling(self):
        """Test handling of complex payloads."""

        async def test_complex_payload():
            complex_payload = {
                "document": {
                    "project_id": "complex_project_456",
                    "nested": {
                        "data": {"key1": "value1", "key2": [1, 2, 3]},
                        "metadata": {"timestamp": "2025-07-24", "version": 2},
                    },
                    "array_field": [{"item": 1}, {"item": 2}],
                },
                "module_location": "lib.realms.complex_realm",
                "extra_field": "ignored",
            }

            mock_realm_class = Mock()
            mock_realm_instance = Mock()
            mock_realm_instance.proceed = True
            mock_realm_instance.launch_template = AsyncMock()
            mock_realm_class.return_value = mock_realm_instance
            self.mock_ygg.load_realm_class.return_value = mock_realm_class

            await self.handler.handle_task(complex_payload)

            # Should pass complete document to realm
            mock_realm_class.assert_called_once_with(
                complex_payload["document"], self.mock_ydm_instance
            )

        asyncio.run(test_complex_payload())

    def test_realm_instance_attribute_error(self):
        """Test handling when realm instance doesn't have proceed attribute."""

        async def test_attribute_error():
            # Mock realm without proceed attribute
            mock_realm_class = Mock()
            mock_realm_instance = Mock(spec=[])  # Empty spec, no attributes
            mock_realm_class.return_value = mock_realm_instance
            self.mock_ygg.load_realm_class.return_value = mock_realm_class

            await self.handler.handle_task(self.valid_payload)

            # getattr should return False as default
            self.mock_logger.info.assert_any_call(
                "Realm skipped (proceed=False) for project %s", "test_project_123"
            )

        asyncio.run(test_attribute_error())

    def test_concurrent_execution(self):
        """Test concurrent execution of multiple tasks."""

        async def test_concurrent():
            # Create multiple payloads
            payloads = [
                {
                    "document": {"project_id": f"project_{i}"},
                    "module_location": f"lib.realms.realm_{i}",
                }
                for i in range(3)
            ]

            # Mock realm for each
            mock_realm_classes = []
            for i in range(3):
                mock_realm_class = Mock()
                mock_realm_instance = Mock()
                mock_realm_instance.proceed = True
                mock_realm_instance.launch_template = AsyncMock()
                mock_realm_class.return_value = mock_realm_instance
                mock_realm_classes.append(mock_realm_class)

            self.mock_ygg.load_realm_class.side_effect = mock_realm_classes

            # Execute concurrently
            tasks = [
                asyncio.create_task(self.handler.handle_task(payload))
                for payload in payloads
            ]
            await asyncio.gather(*tasks)

            # All should have been processed
            self.assertEqual(self.mock_ygg.load_realm_class.call_count, 3)
            self.assertEqual(self.mock_logger.info.call_count, 9)  # 3 calls per task

        asyncio.run(test_concurrent())

    # =====================================================
    # LOGGING VERIFICATION TESTS
    # =====================================================

    def test_logging_levels_and_messages(self):
        """Test that appropriate logging levels are used."""

        async def test_logging():
            # Test warning for invalid payload
            await self.handler.handle_task({"invalid": "payload"})
            self.mock_logger.warning.assert_called()

            # Reset mock
            self.mock_logger.reset_mock()

            # Test error for realm loading failure
            self.mock_ygg.load_realm_class.return_value = None
            await self.handler.handle_task(self.valid_payload)
            self.mock_logger.error.assert_called()

            # Reset mock
            self.mock_logger.reset_mock()

            # Test info for successful execution
            mock_realm_class = Mock()
            mock_realm_instance = Mock()
            mock_realm_instance.proceed = True
            mock_realm_instance.launch_template = AsyncMock()
            mock_realm_class.return_value = mock_realm_instance
            self.mock_ygg.load_realm_class.return_value = mock_realm_class

            await self.handler.handle_task(self.valid_payload)

            # Should have multiple info calls
            self.assertTrue(self.mock_logger.info.call_count >= 3)

        asyncio.run(test_logging())

    def test_logger_name_configuration(self):
        """Test that logger is configured with correct name."""
        # Logger should be created with specific name
        self.mock_logger_factory.assert_called_with("BPA-Handler")

        # Handler should use this logger
        self.assertIs(self.handler.logger, self.mock_logger)


if __name__ == "__main__":
    unittest.main()

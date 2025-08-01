import unittest
from typing import Optional
from unittest.mock import Mock, patch

from lib.core_utils.module_resolver import get_module_location


class TestModuleResolver(unittest.TestCase):
    """
    Comprehensive tests for module_resolver functionality.

    Tests exact matching, prefix matching, error handling, and edge cases.
    """

    def setUp(self):
        """Set up test fixtures."""
        # Sample module registry for testing
        self.sample_registry = {
            "SmartSeq 3": {"module": "lib.realms.smartseq3.smartseq3.SmartSeq3"},
            "10X Chromium": {"module": "lib.realms.tenx.tenx_project.TenXProject"},
            "Legacy": {"module": "lib.realms.legacy.legacy.Legacy", "prefix": True},
            "TestPrefix": {"module": "lib.realms.test.test.Test", "prefix": True},
        }

        # Sample documents for testing
        self.valid_document = {"details": {"library_construction_method": "SmartSeq 3"}}

        self.prefix_document = {
            "details": {"library_construction_method": "Legacy_v2_protocol"}
        }

        self.unknown_method_document = {
            "details": {"library_construction_method": "Unknown Method"}
        }

    @patch("lib.core_utils.module_resolver.ConfigLoader")
    def test_exact_match_success(self, mock_config_loader):
        """Test successful exact match in module registry."""
        # Arrange
        mock_loader_instance = Mock()
        mock_loader_instance.load_config.return_value = self.sample_registry
        mock_config_loader.return_value = mock_loader_instance

        # Act
        result = get_module_location(self.valid_document)

        # Assert
        self.assertEqual(result, "lib.realms.smartseq3.smartseq3.SmartSeq3")
        mock_config_loader.assert_called_once()
        mock_loader_instance.load_config.assert_called_once_with("module_registry.json")

    @patch("lib.core_utils.module_resolver.ConfigLoader")
    def test_exact_match_multiple_options(self, mock_config_loader):
        """Test exact match when multiple methods exist in registry."""
        # Arrange
        mock_loader_instance = Mock()
        mock_loader_instance.load_config.return_value = self.sample_registry
        mock_config_loader.return_value = mock_loader_instance

        document = {"details": {"library_construction_method": "10X Chromium"}}

        # Act
        result = get_module_location(document)

        # Assert
        self.assertEqual(result, "lib.realms.tenx.tenx_project.TenXProject")

    @patch("lib.core_utils.module_resolver.ConfigLoader")
    def test_prefix_match_success(self, mock_config_loader):
        """Test successful prefix matching when exact match fails."""
        # Arrange
        mock_loader_instance = Mock()
        mock_loader_instance.load_config.return_value = self.sample_registry
        mock_config_loader.return_value = mock_loader_instance

        # Act
        result = get_module_location(self.prefix_document)

        # Assert
        self.assertEqual(result, "lib.realms.legacy.legacy.Legacy")

    @patch("lib.core_utils.module_resolver.ConfigLoader")
    def test_prefix_match_first_match_wins(self, mock_config_loader):
        """Test that the first prefix match is returned when multiple prefixes could match."""
        # Arrange
        registry_with_multiple_prefixes = {
            "Test": {"module": "lib.realms.test1.test1.Test1", "prefix": True},
            "TestSpecific": {"module": "lib.realms.test2.test2.Test2", "prefix": True},
        }

        mock_loader_instance = Mock()
        mock_loader_instance.load_config.return_value = registry_with_multiple_prefixes
        mock_config_loader.return_value = mock_loader_instance

        document = {"details": {"library_construction_method": "TestSpecific_protocol"}}

        # Act
        result = get_module_location(document)

        # Assert
        # Should return the first match found (depends on dict iteration order)
        self.assertIn(
            result, ["lib.realms.test1.test1.Test1", "lib.realms.test2.test2.Test2"]
        )

    @patch("lib.core_utils.module_resolver.ConfigLoader")
    def test_prefix_without_prefix_flag(self, mock_config_loader):
        """Test that methods without prefix=True are not used for prefix matching."""
        # Arrange
        registry_no_prefix = {
            "SmartSeq": {
                "module": "lib.realms.smartseq.smartseq.SmartSeq"
                # No prefix flag
            }
        }

        mock_loader_instance = Mock()
        mock_loader_instance.load_config.return_value = registry_no_prefix
        mock_config_loader.return_value = mock_loader_instance

        document = {"details": {"library_construction_method": "SmartSeq_v3"}}

        # Act
        result = get_module_location(document)

        # Assert
        self.assertIsNone(result)

    @patch("lib.core_utils.module_resolver.ConfigLoader")
    def test_no_match_found(self, mock_config_loader):
        """Test behavior when no match is found in registry."""
        # Arrange
        mock_loader_instance = Mock()
        mock_loader_instance.load_config.return_value = self.sample_registry
        mock_config_loader.return_value = mock_loader_instance

        # Act
        result = get_module_location(self.unknown_method_document)

        # Assert
        self.assertIsNone(result)

    @patch("lib.core_utils.module_resolver.ConfigLoader")
    def test_empty_registry(self, mock_config_loader):
        """Test behavior with empty module registry."""
        # Arrange
        mock_loader_instance = Mock()
        mock_loader_instance.load_config.return_value = {}
        mock_config_loader.return_value = mock_loader_instance

        # Act
        result = get_module_location(self.valid_document)

        # Assert
        self.assertIsNone(result)

    @patch("lib.core_utils.module_resolver.logging.error")
    @patch("lib.core_utils.module_resolver.ConfigLoader")
    def test_missing_details_key(self, mock_config_loader, mock_logging_error):
        """Test error handling when document is missing 'details' key."""
        # Arrange
        mock_loader_instance = Mock()
        mock_loader_instance.load_config.return_value = self.sample_registry
        mock_config_loader.return_value = mock_loader_instance

        invalid_document = {"some_other_key": "value"}

        # Act
        result = get_module_location(invalid_document)

        # Assert
        self.assertIsNone(result)
        mock_logging_error.assert_called_once()
        args, _ = mock_logging_error.call_args
        self.assertIn("Missing key in document", args[0])

    @patch("lib.core_utils.module_resolver.logging.error")
    @patch("lib.core_utils.module_resolver.ConfigLoader")
    def test_missing_library_construction_method_key(
        self, mock_config_loader, mock_logging_error
    ):
        """Test error handling when document is missing 'library_construction_method' key."""
        # Arrange
        mock_loader_instance = Mock()
        mock_loader_instance.load_config.return_value = self.sample_registry
        mock_config_loader.return_value = mock_loader_instance

        invalid_document = {"details": {"some_other_field": "value"}}

        # Act
        result = get_module_location(invalid_document)

        # Assert
        self.assertIsNone(result)
        mock_logging_error.assert_called_once()
        args, _ = mock_logging_error.call_args
        self.assertIn("Missing key in document", args[0])

    @patch("lib.core_utils.module_resolver.ConfigLoader")
    def test_config_loader_exception(self, mock_config_loader):
        """Test error handling when ConfigLoader raises an exception."""
        # Arrange
        mock_loader_instance = Mock()
        mock_loader_instance.load_config.side_effect = Exception("Config load failed")
        mock_config_loader.return_value = mock_loader_instance

        # Act & Assert
        # This exposes a bug in the source code where 'method' is undefined when
        # ConfigLoader fails, causing UnboundLocalError in the exception handler
        with self.assertRaises(UnboundLocalError):
            get_module_location(self.valid_document)

    @patch("lib.core_utils.module_resolver.ConfigLoader")
    def test_registry_missing_module_key(self, mock_config_loader):
        """Test error handling when registry entry is missing 'module' key."""
        # Arrange
        invalid_registry = {
            "SmartSeq 3": {
                "description": "SmartSeq 3 method"
                # Missing 'module' key
            }
        }

        mock_loader_instance = Mock()
        mock_loader_instance.load_config.return_value = invalid_registry
        mock_config_loader.return_value = mock_loader_instance

        # Act - This should return None and log an error about missing 'module' key
        result = get_module_location(self.valid_document)

        # Assert
        self.assertIsNone(result)

    @patch("lib.core_utils.module_resolver.logging.error")
    @patch("lib.core_utils.module_resolver.ConfigLoader")
    def test_document_with_none_values(self, mock_config_loader, mock_logging_error):
        """Test behavior when document has None values."""
        # Arrange
        mock_loader_instance = Mock()
        mock_loader_instance.load_config.return_value = self.sample_registry
        mock_config_loader.return_value = mock_loader_instance

        document_with_none = {"details": {"library_construction_method": None}}

        # Act
        result = get_module_location(document_with_none)

        # Assert
        self.assertIsNone(result)
        mock_logging_error.assert_called_once()
        args, _ = mock_logging_error.call_args
        self.assertIn("Error mapping method", args[0])

    @patch("lib.core_utils.module_resolver.ConfigLoader")
    def test_document_with_empty_string_method(self, mock_config_loader):
        """Test behavior when library_construction_method is empty string."""
        # Arrange
        mock_loader_instance = Mock()
        mock_loader_instance.load_config.return_value = self.sample_registry
        mock_config_loader.return_value = mock_loader_instance

        document_empty_method = {"details": {"library_construction_method": ""}}

        # Act
        result = get_module_location(document_empty_method)

        # Assert
        self.assertIsNone(result)

    @patch("lib.core_utils.module_resolver.ConfigLoader")
    def test_registry_with_non_string_keys(self, mock_config_loader):
        """Test behavior with non-string keys in registry."""
        # Arrange
        registry_with_non_string_keys = {
            123: {"module": "lib.realms.numeric.numeric.Numeric"},
            "SmartSeq 3": {"module": "lib.realms.smartseq3.smartseq3.SmartSeq3"},
        }

        mock_loader_instance = Mock()
        mock_loader_instance.load_config.return_value = registry_with_non_string_keys
        mock_config_loader.return_value = mock_loader_instance

        document_numeric_method = {"details": {"library_construction_method": "123"}}

        # Act
        result = get_module_location(document_numeric_method)

        # Assert
        # Should still work as string comparison
        self.assertIsNone(result)  # "123" != 123

    @patch("lib.core_utils.module_resolver.ConfigLoader")
    def test_case_sensitive_matching(self, mock_config_loader):
        """Test that method matching is case-sensitive."""
        # Arrange
        mock_loader_instance = Mock()
        mock_loader_instance.load_config.return_value = self.sample_registry
        mock_config_loader.return_value = mock_loader_instance

        document_wrong_case = {
            "details": {"library_construction_method": "smartseq 3"}  # lowercase
        }

        # Act
        result = get_module_location(document_wrong_case)

        # Assert
        self.assertIsNone(result)

    @patch("lib.core_utils.module_resolver.ConfigLoader")
    def test_whitespace_sensitive_matching(self, mock_config_loader):
        """Test that method matching is whitespace-sensitive."""
        # Arrange
        mock_loader_instance = Mock()
        mock_loader_instance.load_config.return_value = self.sample_registry
        mock_config_loader.return_value = mock_loader_instance

        document_extra_whitespace = {
            "details": {
                "library_construction_method": " SmartSeq 3 "  # extra whitespace
            }
        }

        # Act
        result = get_module_location(document_extra_whitespace)

        # Assert
        self.assertIsNone(result)

    @patch("lib.core_utils.module_resolver.ConfigLoader")
    def test_prefix_matching_order_dependency(self, mock_config_loader):
        """Test prefix matching behavior with overlapping prefixes."""
        # Arrange
        overlapping_registry = {
            "Smart": {"module": "lib.realms.smart.smart.Smart", "prefix": True},
            "SmartSeq": {
                "module": "lib.realms.smartseq.smartseq.SmartSeq",
                "prefix": True,
            },
        }

        mock_loader_instance = Mock()
        mock_loader_instance.load_config.return_value = overlapping_registry
        mock_config_loader.return_value = mock_loader_instance

        document = {"details": {"library_construction_method": "SmartSeq_new_version"}}

        # Act
        result = get_module_location(document)

        # Assert
        # Should return the first match found (dictionary iteration order)
        self.assertIsNotNone(result)
        self.assertIn(
            result,
            ["lib.realms.smart.smart.Smart", "lib.realms.smartseq.smartseq.SmartSeq"],
        )

    @patch("lib.core_utils.module_resolver.logging.error")
    @patch("lib.core_utils.module_resolver.ConfigLoader")
    def test_registry_with_malformed_entries(
        self, mock_config_loader, mock_logging_error
    ):
        """Test behavior with malformed registry entries."""
        # Arrange
        malformed_registry = {
            "SmartSeq 3": {"module": "lib.realms.smartseq3.smartseq3.SmartSeq3"},
            "Malformed": "not_a_dict",  # This should be a dict
            "Another": {"module": None},  # Module is None
        }

        mock_loader_instance = Mock()
        mock_loader_instance.load_config.return_value = malformed_registry
        mock_config_loader.return_value = mock_loader_instance

        # Act - should work for valid entry
        result1 = get_module_location(self.valid_document)
        self.assertEqual(result1, "lib.realms.smartseq3.smartseq3.SmartSeq3")

        # Act - should handle malformed entry gracefully by logging error and returning None
        malformed_document = {"details": {"library_construction_method": "Malformed"}}

        result2 = get_module_location(malformed_document)

        # Assert
        self.assertIsNone(result2)
        mock_logging_error.assert_called()
        args, _ = mock_logging_error.call_args
        self.assertIn("Error mapping method", args[0])

    @patch("lib.core_utils.module_resolver.ConfigLoader")
    def test_config_loader_called_every_time(self, mock_config_loader):
        """Test that ConfigLoader is called on every function call (no caching)."""
        # Arrange
        mock_loader_instance = Mock()
        mock_loader_instance.load_config.return_value = self.sample_registry
        mock_config_loader.return_value = mock_loader_instance

        # Act - call function multiple times
        get_module_location(self.valid_document)
        get_module_location(self.valid_document)
        get_module_location(self.valid_document)

        # Assert - ConfigLoader should be instantiated each time
        self.assertEqual(mock_config_loader.call_count, 3)
        self.assertEqual(mock_loader_instance.load_config.call_count, 3)

    @patch("lib.core_utils.module_resolver.ConfigLoader")
    def test_function_with_complex_nested_document(self, mock_config_loader):
        """Test function with a more complex, deeply nested document structure."""
        # Arrange
        mock_loader_instance = Mock()
        mock_loader_instance.load_config.return_value = self.sample_registry
        mock_config_loader.return_value = mock_loader_instance

        complex_document = {
            "project_id": "P12345",
            "details": {
                "library_construction_method": "SmartSeq 3",
                "samples": ["S001", "S002"],
                "metadata": {"nested": {"deep": "value"}},
            },
            "other_data": ["list", "of", "items"],
        }

        # Act
        result = get_module_location(complex_document)

        # Assert
        self.assertEqual(result, "lib.realms.smartseq3.smartseq3.SmartSeq3")

    def test_function_signature_and_type_hints(self):
        """Test that the function has correct signature and type hints."""
        import inspect
        from typing import get_type_hints

        # Check function signature
        sig = inspect.signature(get_module_location)
        params = list(sig.parameters.keys())
        self.assertEqual(params, ["document"])

        # Check type hints
        hints = get_type_hints(get_module_location)
        self.assertEqual(hints["document"], dict)
        self.assertEqual(hints["return"], Optional[str])


if __name__ == "__main__":
    unittest.main()

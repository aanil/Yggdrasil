import asyncio
import unittest
from unittest.mock import MagicMock, patch

from lib.core_utils.singleton_decorator import SingletonMeta
from lib.couchdb.project_db_manager import ProjectDBManager


class TestProjectDBManager(unittest.IsolatedAsyncioTestCase):
    """
    Comprehensive tests for ProjectDBManager class.
    Tests initialization, async change fetching, document retrieval, and error handling.
    """

    def setUp(self):
        """Set up test fixtures and clear singleton instances for test isolation."""
        # Clear singleton instances to ensure test isolation
        from lib.couchdb.couchdb_connection import CouchDBConnectionManager

        if CouchDBConnectionManager in SingletonMeta._instances:
            del SingletonMeta._instances[CouchDBConnectionManager]

        # Mock module registry data
        self.mock_module_registry = {
            "10X": {"module": "lib.realms.tenx.tenx_project.TenXProject"},
            "Smart-seq3": {
                "module": "lib.realms.smartseq3.smartseq3_project.SmartSeq3Project"
            },
            "MARS": {
                "module": "lib.realms.mars.mars_project.MarsProject",
                "prefix": True,
            },
        }

        # Mock database documents
        self.mock_doc_with_10x = {
            "_id": "doc1",
            "project_id": "P12345",
            "details": {"library_construction_method": "10X"},
        }

        self.mock_doc_with_smartseq = {
            "_id": "doc2",
            "project_id": "P12346",
            "details": {"library_construction_method": "Smart-seq3"},
        }

        self.mock_doc_with_prefix_match = {
            "_id": "doc3",
            "project_id": "P12347",
            "details": {"library_construction_method": "MARS-seq"},
        }

        self.mock_doc_with_unknown_method = {
            "_id": "doc4",
            "project_id": "P12348",
            "details": {"library_construction_method": "UnknownMethod"},
        }

        self.mock_doc_missing_details = {"_id": "doc5", "project_id": "P12349"}

    def tearDown(self):
        """Clean up singleton instances after each test."""
        from lib.couchdb.couchdb_connection import CouchDBConnectionManager

        if CouchDBConnectionManager in SingletonMeta._instances:
            del SingletonMeta._instances[CouchDBConnectionManager]

    @patch("lib.couchdb.project_db_manager.ConfigLoader")
    @patch("lib.couchdb.project_db_manager.CouchDBHandler.__init__")
    def test_init_success(self, mock_handler_init, mock_config_loader):
        """Test successful initialization of ProjectDBManager."""
        # Arrange
        mock_handler_init.return_value = None
        mock_config_instance = MagicMock()
        mock_config_instance.load_config.return_value = self.mock_module_registry
        mock_config_loader.return_value = mock_config_instance

        # Act
        manager = ProjectDBManager()

        # Assert
        mock_handler_init.assert_called_once_with("projects")
        mock_config_instance.load_config.assert_called_once_with("module_registry.json")
        self.assertEqual(manager.module_registry, self.mock_module_registry)

    @patch("lib.couchdb.project_db_manager.ConfigLoader")
    @patch("lib.couchdb.project_db_manager.CouchDBHandler.__init__")
    def test_init_config_loading_error(self, mock_handler_init, mock_config_loader):
        """Test initialization when module registry loading fails."""
        # Arrange
        mock_handler_init.return_value = None
        mock_config_instance = MagicMock()
        mock_config_instance.load_config.side_effect = Exception("Config error")
        mock_config_loader.return_value = mock_config_instance

        # Act & Assert
        with self.assertRaises(Exception):
            ProjectDBManager()

    @patch("lib.couchdb.project_db_manager.ConfigLoader")
    @patch("lib.couchdb.project_db_manager.CouchDBHandler.__init__")
    async def test_fetch_changes_exact_match(
        self, mock_handler_init, mock_config_loader
    ):
        """Test fetch_changes with exact module registry match."""
        # Arrange
        mock_handler_init.return_value = None
        mock_config_instance = MagicMock()
        mock_config_instance.load_config.return_value = self.mock_module_registry
        mock_config_loader.return_value = mock_config_instance

        manager = ProjectDBManager()

        # Mock get_changes to yield our test document
        async def mock_get_changes(last_processed_seq=None):
            yield self.mock_doc_with_10x

        manager.get_changes = mock_get_changes

        # Act
        results = []
        async for doc, module_loc in manager.fetch_changes():
            results.append((doc, module_loc))
            break  # Only get first result

        # Assert
        self.assertEqual(len(results), 1)
        doc, module_loc = results[0]
        self.assertEqual(doc, self.mock_doc_with_10x)
        self.assertEqual(module_loc, "lib.realms.tenx.tenx_project.TenXProject")

    @patch("lib.couchdb.project_db_manager.ConfigLoader")
    @patch("lib.couchdb.project_db_manager.CouchDBHandler.__init__")
    async def test_fetch_changes_prefix_match(
        self, mock_handler_init, mock_config_loader
    ):
        """Test fetch_changes with prefix matching when exact match fails."""
        # Arrange
        mock_handler_init.return_value = None
        mock_config_instance = MagicMock()
        mock_config_instance.load_config.return_value = self.mock_module_registry
        mock_config_loader.return_value = mock_config_instance

        manager = ProjectDBManager()

        # Mock get_changes to yield document with prefix-matchable method
        async def mock_get_changes(last_processed_seq=None):
            yield self.mock_doc_with_prefix_match

        manager.get_changes = mock_get_changes

        # Act
        results = []
        async for doc, module_loc in manager.fetch_changes():
            results.append((doc, module_loc))
            break

        # Assert
        self.assertEqual(len(results), 1)
        doc, module_loc = results[0]
        self.assertEqual(doc, self.mock_doc_with_prefix_match)
        self.assertEqual(module_loc, "lib.realms.mars.mars_project.MarsProject")

    @patch("lib.couchdb.project_db_manager.ConfigLoader")
    @patch("lib.couchdb.project_db_manager.CouchDBHandler.__init__")
    async def test_fetch_changes_no_match(self, mock_handler_init, mock_config_loader):
        """Test fetch_changes when no module registry match is found."""
        # Arrange
        mock_handler_init.return_value = None
        mock_config_instance = MagicMock()
        mock_config_instance.load_config.return_value = self.mock_module_registry
        mock_config_loader.return_value = mock_config_instance

        manager = ProjectDBManager()

        # Mock get_changes to yield one document, then block forever (simulating real CouchDB behavior)
        yielded_count = 0

        async def mock_get_changes(last_processed_seq=None):
            nonlocal yielded_count
            if yielded_count == 0:
                yielded_count += 1
                yield self.mock_doc_with_unknown_method
            # After first call, block forever to simulate waiting for new changes
            await asyncio.sleep(10)  # Long sleep to simulate blocking

        manager.get_changes = mock_get_changes

        # Act - use asyncio.wait_for with timeout to test

        results = []

        try:
            # Try to get results but timeout quickly since we expect none
            async with asyncio.timeout(0.2):
                async for doc, module_loc in manager.fetch_changes():
                    results.append((doc, module_loc))
                    # If we get any results, something is wrong
                    if len(results) > 0:
                        break
        except TimeoutError:
            # Expected - should timeout because no valid results and then blocking
            pass

        # Assert - no results should be yielded for unknown methods
        self.assertEqual(len(results), 0)

    @patch("lib.couchdb.project_db_manager.ConfigLoader")
    @patch("lib.couchdb.project_db_manager.CouchDBHandler.__init__")
    async def test_fetch_changes_missing_details(
        self, mock_handler_init, mock_config_loader
    ):
        """Test fetch_changes when document is missing details/method."""
        # Arrange
        mock_handler_init.return_value = None
        mock_config_instance = MagicMock()
        mock_config_instance.load_config.return_value = self.mock_module_registry
        mock_config_loader.return_value = mock_config_instance

        manager = ProjectDBManager()

        # Mock get_changes to yield one document, then block forever
        yielded_count = 0

        async def mock_get_changes(last_processed_seq=None):
            nonlocal yielded_count
            if yielded_count == 0:
                yielded_count += 1
                yield self.mock_doc_missing_details
            # After first call, block forever to simulate waiting for new changes
            await asyncio.sleep(10)  # Long sleep to simulate blocking

        manager.get_changes = mock_get_changes

        # Act - use asyncio.wait_for with timeout to test

        results = []

        try:
            # Try to get results but timeout quickly since we expect none
            async with asyncio.timeout(0.2):
                async for doc, module_loc in manager.fetch_changes():
                    results.append((doc, module_loc))
                    # If we get any results, something is wrong
                    if len(results) > 0:
                        break
        except TimeoutError:
            # Expected - should timeout because no valid results and then blocking
            pass

        # Assert - no results should be yielded for malformed documents
        self.assertEqual(len(results), 0)

    @patch("lib.couchdb.project_db_manager.ConfigLoader")
    @patch("lib.couchdb.project_db_manager.CouchDBHandler.__init__")
    @patch("lib.couchdb.project_db_manager.Ygg.get_last_processed_seq")
    @patch("lib.couchdb.project_db_manager.Ygg.save_last_processed_seq")
    async def test_get_changes_success(
        self, mock_save_seq, mock_get_seq, mock_handler_init, mock_config_loader
    ):
        """Test get_changes successfully fetches and yields documents."""
        # Arrange
        mock_handler_init.return_value = None
        mock_config_instance = MagicMock()
        mock_config_instance.load_config.return_value = self.mock_module_registry
        mock_config_loader.return_value = mock_config_instance

        mock_get_seq.return_value = "0"

        manager = ProjectDBManager()

        # Mock database changes and get methods
        mock_db = MagicMock()
        mock_changes = [{"id": "doc1", "seq": "1"}, {"id": "doc2", "seq": "2"}]
        mock_db.changes.return_value = mock_changes
        mock_db.get.side_effect = [self.mock_doc_with_10x, self.mock_doc_with_smartseq]
        manager.db = mock_db

        # Act
        results = []
        async for doc in manager.get_changes():
            results.append(doc)
            if len(results) >= 2:  # Get first 2 results
                break

        # Assert
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0], self.mock_doc_with_10x)
        self.assertEqual(results[1], self.mock_doc_with_smartseq)

        # Verify sequence tracking
        mock_db.changes.assert_called_once_with(
            feed="continuous", include_docs=False, since="0"
        )
        self.assertEqual(mock_save_seq.call_count, 2)
        mock_save_seq.assert_any_call("1")
        mock_save_seq.assert_any_call("2")

    @patch("lib.couchdb.project_db_manager.ConfigLoader")
    @patch("lib.couchdb.project_db_manager.CouchDBHandler.__init__")
    @patch("lib.couchdb.project_db_manager.Ygg.get_last_processed_seq")
    async def test_get_changes_with_provided_seq(
        self, mock_get_seq, mock_handler_init, mock_config_loader
    ):
        """Test get_changes when last_processed_seq is provided."""
        # Arrange
        mock_handler_init.return_value = None
        mock_config_instance = MagicMock()
        mock_config_instance.load_config.return_value = self.mock_module_registry
        mock_config_loader.return_value = mock_config_instance

        manager = ProjectDBManager()

        # Mock database
        mock_db = MagicMock()
        mock_db.changes.return_value = []
        manager.db = mock_db

        # Act
        results = []
        async for doc in manager.get_changes(last_processed_seq="custom_seq"):
            results.append(doc)
            break  # Safety break

        # Assert
        # Should not call get_last_processed_seq when seq is provided
        mock_get_seq.assert_not_called()
        mock_db.changes.assert_called_once_with(
            feed="continuous", include_docs=False, since="custom_seq"
        )

    @patch("lib.couchdb.project_db_manager.ConfigLoader")
    @patch("lib.couchdb.project_db_manager.CouchDBHandler.__init__")
    @patch("lib.couchdb.project_db_manager.Ygg.get_last_processed_seq")
    @patch("lib.couchdb.project_db_manager.Ygg.save_last_processed_seq")
    @patch("lib.couchdb.project_db_manager.logging")
    async def test_get_changes_none_document(
        self,
        mock_logging,
        mock_save_seq,
        mock_get_seq,
        mock_handler_init,
        mock_config_loader,
    ):
        """Test get_changes when database returns None for a document."""
        # Arrange
        mock_handler_init.return_value = None
        mock_config_instance = MagicMock()
        mock_config_instance.load_config.return_value = self.mock_module_registry
        mock_config_loader.return_value = mock_config_instance

        mock_get_seq.return_value = "0"

        manager = ProjectDBManager()

        # Mock database to return None document
        mock_db = MagicMock()
        mock_db.changes.return_value = [{"id": "missing_doc", "seq": "1"}]
        mock_db.get.return_value = None
        manager.db = mock_db

        # Act
        results = []
        async for doc in manager.get_changes():
            results.append(doc)
            break  # Safety break since we won't get any real results

        # Assert
        self.assertEqual(len(results), 0)  # No documents should be yielded
        mock_logging.warning.assert_called_with("Document with ID missing_doc is None.")
        mock_save_seq.assert_called_once_with("1")

    @patch("lib.couchdb.project_db_manager.ConfigLoader")
    @patch("lib.couchdb.project_db_manager.CouchDBHandler.__init__")
    @patch("lib.couchdb.project_db_manager.Ygg.get_last_processed_seq")
    @patch("lib.couchdb.project_db_manager.Ygg.save_last_processed_seq")
    @patch("lib.couchdb.project_db_manager.logging")
    async def test_get_changes_none_sequence(
        self,
        mock_logging,
        mock_save_seq,
        mock_get_seq,
        mock_handler_init,
        mock_config_loader,
    ):
        """Test get_changes when sequence is None."""
        # Arrange
        mock_handler_init.return_value = None
        mock_config_instance = MagicMock()
        mock_config_instance.load_config.return_value = self.mock_module_registry
        mock_config_loader.return_value = mock_config_instance

        mock_get_seq.return_value = "0"

        manager = ProjectDBManager()

        # Mock database with None sequence
        mock_db = MagicMock()
        mock_db.changes.return_value = [{"id": "doc1", "seq": None}]
        mock_db.get.return_value = self.mock_doc_with_10x
        manager.db = mock_db

        # Act
        results = []
        async for doc in manager.get_changes():
            results.append(doc)
            break

        # Assert
        self.assertEqual(len(results), 1)
        mock_logging.warning.assert_called_with(
            "Received `None` for last_processed_seq. Skipping save."
        )
        mock_save_seq.assert_not_called()

    @patch("lib.couchdb.project_db_manager.ConfigLoader")
    @patch("lib.couchdb.project_db_manager.CouchDBHandler.__init__")
    @patch("lib.couchdb.project_db_manager.Ygg.get_last_processed_seq")
    @patch("lib.couchdb.project_db_manager.logging")
    async def test_get_changes_db_exception(
        self, mock_logging, mock_get_seq, mock_handler_init, mock_config_loader
    ):
        """Test get_changes when database operations raise exceptions."""
        # Arrange
        mock_handler_init.return_value = None
        mock_config_instance = MagicMock()
        mock_config_instance.load_config.return_value = self.mock_module_registry
        mock_config_loader.return_value = mock_config_instance

        mock_get_seq.return_value = "0"

        manager = ProjectDBManager()

        # Mock database to raise exception on get
        mock_db = MagicMock()
        mock_change = {"id": "error_doc", "seq": "1"}
        mock_db.changes.return_value = [mock_change]
        mock_db.get.side_effect = Exception("Database error")
        manager.db = mock_db

        # Act
        results = []
        async for doc in manager.get_changes():
            results.append(doc)
            break  # Safety break

        # Assert
        self.assertEqual(len(results), 0)  # No documents should be yielded
        mock_logging.warning.assert_called_with(
            "Error processing change: Database error"
        )
        mock_logging.debug.assert_called_with(f"Data causing the error: {mock_change}")

    @patch("lib.couchdb.project_db_manager.ConfigLoader")
    @patch("lib.couchdb.project_db_manager.CouchDBHandler.__init__")
    def test_fetch_document_by_id_success(self, mock_handler_init, mock_config_loader):
        """Test successful document retrieval by ID."""
        # Arrange
        mock_handler_init.return_value = None
        mock_config_instance = MagicMock()
        mock_config_instance.load_config.return_value = self.mock_module_registry
        mock_config_loader.return_value = mock_config_instance

        manager = ProjectDBManager()

        # Mock database
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = self.mock_doc_with_10x
        manager.db = mock_db

        # Act
        result = manager.fetch_document_by_id("doc1")

        # Assert
        self.assertEqual(result, self.mock_doc_with_10x)
        mock_db.__getitem__.assert_called_once_with("doc1")

    @patch("lib.couchdb.project_db_manager.ConfigLoader")
    @patch("lib.couchdb.project_db_manager.CouchDBHandler.__init__")
    @patch("lib.couchdb.project_db_manager.logging")
    def test_fetch_document_by_id_not_found(
        self, mock_logging, mock_handler_init, mock_config_loader
    ):
        """Test document retrieval when document doesn't exist."""
        # Arrange
        mock_handler_init.return_value = None
        mock_config_instance = MagicMock()
        mock_config_instance.load_config.return_value = self.mock_module_registry
        mock_config_loader.return_value = mock_config_instance

        manager = ProjectDBManager()

        # Mock database to raise KeyError
        mock_db = MagicMock()
        mock_db.__getitem__.side_effect = KeyError("Document not found")
        manager.db = mock_db

        # Act
        result = manager.fetch_document_by_id("nonexistent_doc")

        # Assert
        self.assertIsNone(result)
        mock_logging.error.assert_called_with(
            "Document with ID 'nonexistent_doc' not found in the database."
        )

    @patch("lib.couchdb.project_db_manager.ConfigLoader")
    @patch("lib.couchdb.project_db_manager.CouchDBHandler.__init__")
    @patch("lib.couchdb.project_db_manager.logging")
    def test_fetch_document_by_id_database_error(
        self, mock_logging, mock_handler_init, mock_config_loader
    ):
        """Test document retrieval when database raises an exception."""
        # Arrange
        mock_handler_init.return_value = None
        mock_config_instance = MagicMock()
        mock_config_instance.load_config.return_value = self.mock_module_registry
        mock_config_loader.return_value = mock_config_instance

        manager = ProjectDBManager()

        # Mock database to raise exception
        mock_db = MagicMock()
        mock_db.__getitem__.side_effect = Exception("Database connection error")
        manager.db = mock_db

        # Act
        result = manager.fetch_document_by_id("error_doc")

        # Assert
        self.assertIsNone(result)
        mock_logging.error.assert_called_with(
            "Error while accessing database: Database connection error"
        )

    @patch("lib.couchdb.project_db_manager.ConfigLoader")
    @patch("lib.couchdb.project_db_manager.CouchDBHandler.__init__")
    async def test_fetch_changes_multiple_documents(
        self, mock_handler_init, mock_config_loader
    ):
        """Test fetch_changes with multiple documents of different types."""
        # Arrange
        mock_handler_init.return_value = None
        mock_config_instance = MagicMock()
        mock_config_instance.load_config.return_value = self.mock_module_registry
        mock_config_loader.return_value = mock_config_instance

        manager = ProjectDBManager()

        # Mock get_changes to yield multiple documents
        async def mock_get_changes(last_processed_seq=None):
            yield self.mock_doc_with_10x
            yield self.mock_doc_with_smartseq
            yield self.mock_doc_with_prefix_match
            yield self.mock_doc_with_unknown_method
            yield self.mock_doc_missing_details

        manager.get_changes = mock_get_changes

        # Act
        results = []
        async for doc, module_loc in manager.fetch_changes():
            results.append((doc, module_loc))
            if len(results) >= 3:  # Expect 3 valid results
                break

        # Assert
        self.assertEqual(len(results), 3)

        # Check exact matches
        self.assertEqual(results[0][1], "lib.realms.tenx.tenx_project.TenXProject")
        self.assertEqual(
            results[1][1], "lib.realms.smartseq3.smartseq3_project.SmartSeq3Project"
        )

        # Check prefix match
        self.assertEqual(results[2][1], "lib.realms.mars.mars_project.MarsProject")

    @patch("lib.couchdb.project_db_manager.ConfigLoader")
    @patch("lib.couchdb.project_db_manager.CouchDBHandler.__init__")
    async def test_fetch_changes_empty_module_registry(
        self, mock_handler_init, mock_config_loader
    ):
        """Test fetch_changes with empty module registry."""
        # Arrange
        mock_handler_init.return_value = None
        mock_config_instance = MagicMock()
        mock_config_instance.load_config.return_value = {}  # Empty registry
        mock_config_loader.return_value = mock_config_instance

        manager = ProjectDBManager()

        # Mock get_changes to yield one document, then block forever
        yielded_count = 0

        async def mock_get_changes(last_processed_seq=None):
            nonlocal yielded_count
            if yielded_count == 0:
                yielded_count += 1
                yield self.mock_doc_with_10x
            # After first call, block forever to simulate waiting for new changes
            await asyncio.sleep(10)  # Long sleep to simulate blocking

        manager.get_changes = mock_get_changes

        # Act - use asyncio.wait_for with timeout to test

        results = []

        try:
            # Try to get results but timeout quickly since we expect none
            async with asyncio.timeout(0.2):
                async for doc, module_loc in manager.fetch_changes():
                    results.append((doc, module_loc))
                    # If we get any results, something is wrong
                    if len(results) > 0:
                        break
        except TimeoutError:
            # Expected - should timeout because no valid results and then blocking
            pass

        # Assert - no results should be yielded with empty registry
        self.assertEqual(len(results), 0)


if __name__ == "__main__":
    unittest.main()

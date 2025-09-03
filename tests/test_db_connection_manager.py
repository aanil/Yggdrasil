import unittest
from unittest.mock import MagicMock, patch

from lib.core_utils.singleton_decorator import SingletonMeta
from lib.couchdb.couchdb_connection import CouchDBConnectionManager


class TestCouchDBConnectionManager(unittest.TestCase):
    def setUp(self):
        # Clear singleton instances to ensure test isolation
        if CouchDBConnectionManager in SingletonMeta._instances:
            del SingletonMeta._instances[CouchDBConnectionManager]

        # Common configuration that will be returned by ConfigLoader.load_config
        self.mock_config = {
            "couchdb": {
                "url": "localhost:5984",
                "default_user": "admin",
                "default_password": "secret",
            }
        }

    def tearDown(self):
        # Clear singleton instances after each test
        if CouchDBConnectionManager in SingletonMeta._instances:
            del SingletonMeta._instances[CouchDBConnectionManager]

    @patch(
        "lib.couchdb.couchdb_connection.ConfigLoader.load_config",
        return_value={
            "couchdb": {
                "url": "localhost:5984",
                "default_user": "admin",
                "default_password": "secret",
            }
        },
    )
    @patch("lib.couchdb.couchdb_connection.os.getenv", side_effect=lambda k, d: d)
    @patch("lib.couchdb.couchdb_connection.cloudant_v1.CloudantV1")
    @patch("lib.couchdb.couchdb_connection.CouchDbSessionAuthenticator")
    def test_initialization_with_defaults(
        self, mock_server_class, mock_getenv, mock_load_config
    ):
        # Mock a successful server connection
        mock_server = MagicMock()
        mock_server.version.return_value = "3.1.1"
        mock_server_class.return_value = mock_server

        manager = CouchDBConnectionManager()

        # Verify that the manager used config defaults
        self.assertEqual(manager.db_url, "localhost:5984")
        self.assertEqual(manager.db_user, "admin")
        self.assertEqual(manager.db_password, "secret")

        # Verify that server is connected
        self.assertIsNotNone(manager.server)
        mock_server.version.assert_called_once()

    @patch(
        "lib.couchdb.couchdb_connection.ConfigLoader.load_config",
        return_value={
            "couchdb": {
                "url": "localhost:5984",
                "default_user": "admin",
                "default_password": "secret",
            }
        },
    )
    @patch("lib.couchdb.couchdb_connection.os.getenv", side_effect=lambda k, d: d)
    @patch("lib.couchdb.couchdb_connection.cloudant_v1.CloudantV1")
    @patch("lib.couchdb.couchdb_connection.CouchDbSessionAuthenticator")
    def test_singleton_returns_same_instance(
        self, mock_server_class, mock_getenv, mock_load_config
    ):
        # First instantiation
        mock_server = MagicMock()
        mock_server.version.return_value = "3.1.1"
        mock_server_class.return_value = mock_server

        manager1 = CouchDBConnectionManager()
        manager2 = CouchDBConnectionManager()  # Same instance since it's a singleton

        self.assertIs(manager1, manager2)
        self.assertEqual(manager2.db_url, "localhost:5984")  # Same as manager1
        self.assertEqual(manager2.db_user, "admin")
        self.assertEqual(manager2.db_password, "secret")

    @patch(
        "lib.couchdb.couchdb_connection.ConfigLoader.load_config",
        return_value={
            "couchdb": {
                "url": "localhost:5984",
                "default_user": "admin",
                "default_password": "secret",
            }
        },
    )
    @patch("lib.couchdb.couchdb_connection.os.getenv", side_effect=lambda k, d: d)
    @patch("lib.couchdb.couchdb_connection.cloudant_v1.CloudantV1")
    @patch("lib.couchdb.couchdb_connection.CouchDbSessionAuthenticator")
    def test_connect_server_failure(
        self, mock_server_class, mock_getenv, mock_load_config
    ):
        # Simulate connection failure
        mock_server_class.side_effect = Exception("Connection failed")

        with self.assertRaises(ConnectionError) as cm:
            CouchDBConnectionManager()
        self.assertEqual(str(cm.exception), "Failed to connect to CouchDB server")


if __name__ == "__main__":
    unittest.main()

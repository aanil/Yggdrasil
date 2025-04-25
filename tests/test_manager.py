import unittest
from unittest.mock import MagicMock, patch

import couchdb

from lib.couchdb.couchdb_connection import CouchDBConnectionManager


class TestCouchDBConnectionManager(unittest.TestCase):
    def setUp(self):
        # Common configuration that will be returned by ConfigLoader.load_config
        self.mock_config = {
            "couchdb": {
                "url": "localhost:5984",
                "default_user": "admin",
                "default_password": "secret",
            }
        }

    @patch(
        "lib.couchdb.manager.ConfigLoader.load_config",
        return_value={
            "couchdb": {
                "url": "localhost:5984",
                "default_user": "admin",
                "default_password": "secret",
            }
        },
    )
    @patch("lib.couchdb.manager.os.getenv", side_effect=lambda k, d: d)
    @patch("lib.couchdb.manager.couchdb.Server")
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
        "lib.couchdb.manager.ConfigLoader.load_config",
        return_value={
            "couchdb": {
                "url": "localhost:5984",
                "default_user": "admin",
                "default_password": "secret",
            }
        },
    )
    @patch("lib.couchdb.manager.os.getenv", side_effect=lambda k, d: d)
    @patch("lib.couchdb.manager.couchdb.Server")
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
        "lib.couchdb.manager.ConfigLoader.load_config",
        return_value={
            "couchdb": {
                "url": "localhost:5984",
                "default_user": "admin",
                "default_password": "secret",
            }
        },
    )
    @patch("lib.couchdb.manager.os.getenv", side_effect=lambda k, d: d)
    @patch("lib.couchdb.manager.couchdb.Server")
    def test_connect_server_failure(
        self, mock_server_class, mock_getenv, mock_load_config
    ):
        # Simulate connection failure
        mock_server_class.side_effect = Exception("Connection failed")

        with self.assertRaises(ConnectionError) as cm:
            CouchDBConnectionManager()
        self.assertEqual(str(cm.exception), "Failed to connect to CouchDB server")

    @patch(
        "lib.couchdb.manager.ConfigLoader.load_config",
        return_value={
            "couchdb": {
                "url": "localhost:5984",
                "default_user": "admin",
                "default_password": "secret",
            }
        },
    )
    @patch("lib.couchdb.manager.os.getenv", side_effect=lambda k, d: d)
    @patch("lib.couchdb.manager.couchdb.Server")
    def test_connect_db_success(self, mock_server_class, mock_getenv, mock_load_config):
        # Mock a connected server and a database
        mock_server = MagicMock()
        mock_server.version.return_value = "3.1.1"
        mock_db = MagicMock()
        mock_server.__getitem__.return_value = mock_db
        mock_server_class.return_value = mock_server

        manager = CouchDBConnectionManager()
        db = manager.connect_db("testdb")
        self.assertIs(db, mock_db)
        self.assertIn("testdb", manager.databases)
        self.assertEqual(manager.databases["testdb"], mock_db)

    @patch(
        "lib.couchdb.manager.ConfigLoader.load_config",
        return_value={
            "couchdb": {
                "url": "localhost:5984",
                "default_user": "admin",
                "default_password": "secret",
            }
        },
    )
    @patch("lib.couchdb.manager.os.getenv", side_effect=lambda k, d: d)
    @patch("lib.couchdb.manager.couchdb.Server")
    def test_connect_db_no_server(
        self, mock_server_class, mock_getenv, mock_load_config
    ):
        # Mock a successful initial connection, then remove the server
        mock_server = MagicMock()
        mock_server.version.return_value = "3.1.1"
        mock_server_class.return_value = mock_server

        manager = CouchDBConnectionManager()
        # Simulate losing server connection
        manager.server = None

        with self.assertRaises(ConnectionError) as cm:
            manager.connect_db("testdb")
        self.assertEqual(str(cm.exception), "Server not connected")

    @patch(
        "lib.couchdb.manager.ConfigLoader.load_config",
        return_value={
            "couchdb": {
                "url": "localhost:5984",
                "default_user": "admin",
                "default_password": "secret",
            }
        },
    )
    @patch("lib.couchdb.manager.os.getenv", side_effect=lambda k, d: d)
    @patch("lib.couchdb.manager.couchdb.Server")
    def test_connect_db_not_found(
        self, mock_server_class, mock_getenv, mock_load_config
    ):
        mock_server = MagicMock()
        mock_server.version.return_value = "3.1.1"
        # Simulate that the database does not exist
        mock_server.__getitem__.side_effect = couchdb.http.ResourceNotFound("Not found")
        mock_server_class.return_value = mock_server

        manager = CouchDBConnectionManager()
        with self.assertRaises(ConnectionError) as cm:
            manager.connect_db("missingdb")
        self.assertEqual(str(cm.exception), "Database missingdb does not exist")

    @patch(
        "lib.couchdb.manager.ConfigLoader.load_config",
        return_value={
            "couchdb": {
                "url": "localhost:5984",
                "default_user": "admin",
                "default_password": "secret",
            }
        },
    )
    @patch("lib.couchdb.manager.os.getenv", side_effect=lambda k, d: d)
    @patch("lib.couchdb.manager.couchdb.Server")
    def test_connect_db_unexpected_error(
        self, mock_server_class, mock_getenv, mock_load_config
    ):
        mock_server = MagicMock()
        mock_server.version.return_value = "3.1.1"
        mock_server.__getitem__.side_effect = Exception("Unknown error")
        mock_server_class.return_value = mock_server

        manager = CouchDBConnectionManager()
        with self.assertRaises(ConnectionError) as cm:
            manager.connect_db("errordb")
        self.assertEqual(str(cm.exception), "Could not connect to database errordb")


if __name__ == "__main__":
    unittest.main()

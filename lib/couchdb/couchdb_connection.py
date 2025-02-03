import os
from typing import Dict, Optional

import couchdb

from lib.core_utils.config_loader import ConfigLoader
from lib.core_utils.logging_utils import custom_logger
from lib.core_utils.singleton_decorator import singleton

logging = custom_logger(__name__.split(".")[-1])


@singleton
class CouchDBConnectionManager:
    """
    Handles connections to a CouchDB server, including:

      - Reading configuration for URLs, credentials, and defaults.
      - Creating and storing references to multiple databases.
      - Providing a unified entry point for connecting to CouchDB.

    Automatically calls `connect_server()` on initialization.
    Typical usage involves calling`connect_db(...)` to
    retrieve specific Database objects.
    """

    def __init__(
        self,
        db_url: Optional[str] = None,
        db_user: Optional[str] = None,
        db_password: Optional[str] = None,
    ) -> None:
        # Load defaults from configuration file or environment
        self.db_config = ConfigLoader().load_config("main.json").get("couchdb", {})
        self.db_url = db_url or self.db_config.get("url")
        self.db_user = db_user or os.getenv(
            "COUCH_USER", self.db_config.get("default_user")
        )
        self.db_password = db_password or os.getenv(
            "COUCH_PASS", self.db_config.get("default_password")
        )

        self.server: Optional[couchdb.Server] = None
        self.databases: Dict[str, couchdb.Database] = {}

        self.connect_server()

    def connect_server(self) -> None:
        """Establishes a connection to the CouchDB server."""
        if self.server is None:
            try:
                server_url = f"http://{self.db_user}:{self.db_password}@{self.db_url}"
                self.server = couchdb.Server(server_url)
                version = self.server.version()
                logging.info(f"Connected to CouchDB server. Version: {version}")
            except Exception as e:
                logging.error(
                    f"An error occurred while connecting to the CouchDB server: {e}"
                )
                raise ConnectionError("Failed to connect to CouchDB server")
        else:
            logging.info("Already connected to CouchDB server.")

    def connect_db(self, db_name: str) -> couchdb.Database:
        """Connects to a specific database on the CouchDB server.

        Args:
            db_name (str): The name of the database to connect to.

        Returns:
            couchdb.Database: The connected database instance.

        Raises:
            ConnectionError: If the server is not connected or the database does not exist.
        """
        if db_name not in self.databases:
            if not self.server:
                logging.error(
                    "Server is not connected. Please connect to server first."
                )
                raise ConnectionError("Server not connected")

            try:
                self.databases[db_name] = self.server[db_name]
                logging.info(f"Connected to database: {db_name}")
            except couchdb.http.ResourceNotFound:
                logging.error(f"Database {db_name} does not exist.")
                raise ConnectionError(f"Database {db_name} does not exist")
            except Exception as e:
                logging.error(f"Failed to connect to database {db_name}: {e}")
                raise ConnectionError(f"Could not connect to database {db_name}") from e
        else:
            logging.info(f"Already connected to database: {db_name}")

        return self.databases[db_name]


class CouchDBHandler:
    """
    Base class for CouchDB operations on a specific database.

    Inheriting classes specify a database name and leverage the
    CouchDBConnectionManager to:

      - Obtain a server connection.
      - Connect to the desired database.
      - Store a `db` attribute for further CRUD or custom actions.

    This ensures each subclass references the correct CouchDB database
    instance without duplicating connection logic.
    """

    def __init__(self, db_name: str) -> None:
        self.connection_manager = CouchDBConnectionManager()
        self.db = self.connection_manager.connect_db(db_name)

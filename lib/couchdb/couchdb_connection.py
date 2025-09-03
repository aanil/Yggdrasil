import os

from ibmcloudant import CouchDbSessionAuthenticator, cloudant_v1

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
    """

    def __init__(
        self,
        db_url: str | None = None,
        db_user: str | None = None,
        db_password: str | None = None,
    ) -> None:
        # Load defaults from configuration file or environment
        self.db_config = ConfigLoader().load_config("config.json").get("couchdb", {})
        self.db_url = db_url or self.db_config.get("url")
        self.db_user = db_user or os.getenv(
            "COUCH_USER", self.db_config.get("default_user")
        )
        self.db_password = db_password or os.getenv(
            "COUCH_PASS", self.db_config.get("default_password")
        )

        self.server: cloudant_v1.CloudantV1 | None = None

        self.connect_server()

    def connect_server(self) -> None:
        """Establishes a connection to the CouchDB server."""
        if self.server is None:
            try:
                self.server = cloudant_v1.CloudantV1(
                    authenticator=CouchDbSessionAuthenticator(
                        self.db_user, self.db_password
                    )
                )
                self.server.set_service_url(self.db_url)
                version = (
                    self.server.get_server_information().get_result().get("version")
                )
                logging.info(f"Connected to CouchDB server. Version: {version}")
            except Exception as e:
                logging.error(
                    f"An error occurred while connecting to the CouchDB server: {e}"
                )
                raise ConnectionError("Failed to connect to CouchDB server")
        else:
            logging.info("Already connected to CouchDB server.")


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
        self.db_name = db_name

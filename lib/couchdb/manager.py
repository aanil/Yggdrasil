import os
from typing import Any, AsyncGenerator, Dict, Optional, Tuple

import couchdb

from lib.core_utils.common import YggdrasilUtilities as Ygg
from lib.core_utils.config_loader import ConfigLoader
from lib.core_utils.logging_utils import custom_logger
from lib.core_utils.singleton_decorator import singleton
from lib.couchdb.document import YggdrasilDocument

logging = custom_logger(__name__.split(".")[-1])


@singleton
class CouchDBConnectionManager:
    """Manages connections to the CouchDB server and databases."""

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
    """Base class for CouchDB operations."""

    def __init__(self, db_name: str) -> None:
        self.connection_manager = CouchDBConnectionManager()
        self.db = self.connection_manager.connect_db(db_name)


class ProjectDBManager(CouchDBHandler):
    """Manages interactions with the 'projects' database."""

    def __init__(self) -> None:
        super().__init__("projects")
        self.module_registry = ConfigLoader().load_config("module_registry.json")

    async def fetch_changes(self) -> AsyncGenerator[Tuple[Dict[str, Any], str], None]:
        """Fetches document changes from the database asynchronously.

        Yields:
            Tuple[Dict[str, Any], str]: A tuple containing the document and module location.
        """
        last_processed_seq: Optional[str] = None

        while True:
            async for change in self.get_changes(last_processed_seq=last_processed_seq):
                try:
                    method = change["details"]["library_construction_method"]
                    module_config = self.module_registry.get(method)

                    if module_config:
                        module_loc = module_config["module"]
                        yield (change, module_loc)
                    else:
                        # Check for prefix matches
                        for registered_method, config in self.module_registry.items():
                            if config.get("prefix") and method.startswith(
                                registered_method
                            ):
                                module_loc = config["module"]
                                yield (change, module_loc)
                                break
                        else:
                            # The majority of the tasks will not have a module configured.
                            # If you log this, expect to see many messages!
                            # logging.warning(f"No module configured for task type '{method}'.")
                            pass
                except Exception as e:  # noqa: F841
                    # logging.error(f"Error processing change: {e}")
                    pass

    async def get_changes(
        self, last_processed_seq: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Fetch and yield document changes from a CouchDB database.

        Args:
            last_processed_seq (Optional[str]): The sequence number from which to start
                monitoring changes.

        Yields:
            Dict[str, Any]: A document representing a change.
        """
        if last_processed_seq is None:
            last_processed_seq = Ygg.get_last_processed_seq()

        changes = self.db.changes(
            feed="continuous", include_docs=False, since=last_processed_seq
        )

        for change in changes:
            try:
                doc = self.db.get(change["id"])
                last_processed_seq = change["seq"]
                if last_processed_seq is not None:
                    Ygg.save_last_processed_seq(last_processed_seq)
                else:
                    logging.warning(
                        "Received `None` for last_processed_seq. Skipping save."
                    )

                if doc is not None:
                    yield doc
                else:
                    logging.warning(f"Document with ID {change['id']} is None.")
            except Exception as e:
                logging.warning(f"Error processing change: {e}")
                logging.debug(f"Data causing the error: {change}")

    def fetch_document_by_id(self, doc_id):
        """Fetches a document from the database by its ID.

        Args:
            doc_id (str): The ID of the document to fetch.

        Returns:
            Optional[Dict[str, Any]]: The retrieved document, or None if not found.
        """
        try:
            document = self.db[doc_id]
            return document
        except KeyError:
            logging.error(f"Document with ID '{doc_id}' not found in the database.")
            return None
        except Exception as e:
            logging.error(f"Error while accessing database: {e}")
            return None


class YggdrasilDBManager(CouchDBHandler):
    """Manages interactions with the 'yggdrasil' database."""

    def __init__(self) -> None:
        super().__init__("yggdrasil")

    def create_project(
        self, project_id: str, projects_reference: str, method: str
    ) -> YggdrasilDocument:
        """Creates a new project document in the database.

        Args:
            project_id (str): The project ID.
            projects_reference (str): Reference to the original project document.
            method (str): The library construction method.

        Returns:
            YggdrasilDocument: The newly created project document.
        """
        new_document = YggdrasilDocument(
            project_id=project_id, projects_reference=projects_reference, method=method
        )
        self.save_document(new_document)
        logging.info(f"New project with ID '{project_id}' created successfully.")
        return new_document

    def save_document(self, document: YggdrasilDocument) -> None:
        try:
            existing_doc = self.db.get(document._id)
            doc_dict = document.to_dict()
            if existing_doc:
                # Preserve the _rev field to avoid update conflicts
                doc_dict["_rev"] = existing_doc["_rev"]
            self.db.save(doc_dict)
            logging.info(
                f"Document with ID '{document._id}' saved successfully in 'yggdrasil' DB."
            )
        except Exception as e:
            logging.error(f"Error saving document: {e}")

    def get_document_by_project_id(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a document by project ID.

        Args:
            project_id (str): The project ID to search for.

        Returns:
            Optional[Dict[str, Any]]: The document if found, else None.
        """
        try:
            document = self.db[project_id]
            return document
        except couchdb.http.ResourceNotFound:
            logging.info(f"Project with ID '{project_id}' not found.")
            return None
        except Exception as e:
            logging.error(f"Error accessing project: {e}")
            return None

    def add_sample(
        self,
        project_id: str,
        sample_id: str,
        # lib_prep_option: str,
        status: str = "pending",
    ) -> None:
        """Adds a sample to a project and saves the document.

        Args:
            project_id (str): The project ID.
            sample_id (str): The sample ID.
            lib_prep_option (str): The library preparation option.
            status (str, optional): The status of the sample. Defaults to "pending".
        """
        try:
            document_dict = self.get_document_by_project_id(project_id)
            if document_dict:
                ygg_doc = YggdrasilDocument.from_dict(document_dict)
                ygg_doc.add_sample(sample_id, status)
                self.save_document(ygg_doc)
                logging.info(
                    f"Updated project '{project_id}' with sample '{sample_id}'"
                )
            else:
                logging.error(f"Project '{project_id}' does not exist in YggdrasilDB.")
        except Exception as e:
            logging.error(f"Error adding sample: {e}")

    def update_sample_status(
        self, project_id: str, sample_id: str, status: str
    ) -> None:
        """Updates the status of a sample within a project.

        Args:
            project_id (str): The project ID.
            sample_id (str): The sample ID.
            status (str): The new status for the sample.
        """
        try:
            document_dict = self.get_document_by_project_id(project_id)
            if document_dict:
                ygg_doc = YggdrasilDocument.from_dict(document_dict)
                ygg_doc.update_sample_status(sample_id, status)
                self.save_document(ygg_doc)
                logging.info(
                    f"Updated status of sample '{sample_id}' in project '{project_id}' to '{status}'."
                )
            else:
                logging.error(f"Project with ID '{project_id}' not found.")
        except Exception as e:
            logging.error(f"Error updating sample status: {e}")

    def check_project_exists(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Checks if a project exists in the database.

        Args:
            project_id (str): The project ID to check.

        Returns:
            Optional[Dict[str, Any]]: The project document if it exists, else None.
        """
        existing_document = self.get_document_by_project_id(project_id)
        if existing_document:
            logging.info(f"Project with ID '{project_id}' exists.")
            return existing_document
        else:
            logging.info(f"Project with ID '{project_id}' does not exist.")
            return None

    def get_sample_status(self, project_id: str, sample_id: str) -> Optional[str]:
        """Retrieves the status of a specific sample.

        Args:
            project_id (str): The project ID.
            sample_id (str): The sample ID.

        Returns:
            Optional[str]: The status of the sample if found, else None.
        """
        document_dict = self.get_document_by_project_id(project_id)
        if document_dict:
            ygg_doc = YggdrasilDocument.from_dict(document_dict)
            sample = ygg_doc.get_sample(sample_id)
            if sample:
                return sample["status"]
        return None

    def get_project_status(self, project_id: str) -> Optional[str]:
        """Retrieves the status of a project.

        Args:
            project_id (str): The project ID.

        Returns:
            Optional[str]: The status of the project if found, else None.
        """
        document_dict = self.get_document_by_project_id(project_id)
        if document_dict:
            return document_dict.get("status")
        return None

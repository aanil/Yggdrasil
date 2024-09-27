import os
import couchdb

from typing import Optional, Dict, Any

from lib.utils.config_loader import ConfigLoader
from lib.couchdb.document import YggdrasilDocument
from lib.utils.singleton_decorator import singleton
from lib.utils.couch_utils import save_last_processed_seq, get_last_processed_seq, has_required_fields

from lib.utils.logging_utils import custom_logger

logging = custom_logger(__name__.split('.')[-1])

@singleton
class CouchDBConnectionManager:
    def __init__(self, db_url=None, db_user=None, db_password=None):
        # Load defaults from configuration file or environment
        self.db_config = ConfigLoader().load_config("main.json").get("couchdb", {})
        self.db_url = db_url or self.db_config.get("url")
        self.db_user = db_user or os.getenv("COUCH_USER", self.db_config.get("default_user"))
        self.db_password = db_password or os.getenv("COUCH_PASS", self.db_config.get("default_password"))

        self.server = None
        self.databases = {}

        self.connect_server()


    def connect_server(self):
        """Establishes a connection to the CouchDB server."""
        if self.server is None:
            try:
                server_url = f"http://{self.db_user}:{self.db_password}@{self.db_url}"
                self.server = couchdb.Server(server_url)
                version = self.server.version()
                logging.info(f"Connected to CouchDB server. Version: {version}")
            except Exception as e:
                logging.error(f"An error occurred while connecting to the CouchDB server: {e}")
                raise ConnectionError("Failed to connect to CouchDB server")
        else:
            logging.info("Already connected to CouchDB server.")


    def connect_db(self, db_name):
        """Connect to a specific database on the established CouchDB server."""
        if db_name not in self.databases:
            if not self.server:
                logging.error("Server is not connected. Please connect to server first.")
                raise ConnectionError("Server not connected")
            
            try:
                self.databases[db_name] = self.server[db_name]
                logging.info(f"Connected to database: {db_name}")
            except couchdb.http.ResourceNotFound:
                logging.error(f"Database {db_name} does not exist.")
                raise ConnectionError(f"Database {db_name} does not exist")
            except Exception as e:
                logging.error(f"Failed to connect to database {db_name}: {e}")
                raise ConnectionError(f"Could not connect to database {db_name}")
        else:
            logging.info(f"Already connected to database: {db_name}")

        return self.databases[db_name]


class CouchDBHandler:
    def __init__(self, db_name):
        self.connection_manager = CouchDBConnectionManager()
        self.db = self.connection_manager.connect_db(db_name)


class ProjectDBManager(CouchDBHandler):
    def __init__(self):
        super().__init__('projects')
        self.module_registry = ConfigLoader().load_config("module_registry.json")

    async def fetch_changes(self):
        last_processed_seq = None

        while True:
            async for change in self.get_changes(last_processed_seq=last_processed_seq):
                try:
                    method = change['details']['library_construction_method']
                    # TODO: Might error if the method is not found in the registry, use .get() instead
                    module_config = self.module_registry[method]

                    if module_config:
                        module_loc = module_config["module"]
                        yield (change, module_loc)
                    else:
                        # No exact match, check for prefix matches
                        for registered_method, config in self.module_registry.items():
                            if config.get("prefix") and method.startswith(registered_method):
                                module_loc = config["module"]
                                yield (change, module_loc)
                                break
                        else:
                            # The majority of the tasks will not have a module configured.
                            # If you log this, expect to see many messages!
                            # logging.warning(f"No module configured for task type '{method}'.")
                            pass
                except Exception as e:
                    # logging.error(f"Error while processing incoming CouchDB data")
                    # logging.debug(f"Error: {e}")
                    pass


    async def get_changes(self, last_processed_seq=None):
        """
        Fetch and yield document changes from a CouchDB database using the Changes API.

        Args:
            db: The CouchDB database to monitor for changes.
            last_processed_seq (str, optional): The sequence number from which to start
                monitoring changes. If not provided, it will use the last processed
                sequence stored in a configuration file.

        Yields:
            dict: A document representing a change that matches the specified criteria.
        """
        if last_processed_seq is None:
            last_processed_seq = get_last_processed_seq()

        changes = self.db.changes(feed='continuous', include_docs=False, since=last_processed_seq)

        for change in changes:
            try:
                doc = self.db.get(change['id'])
                last_processed_seq = change['seq']
                save_last_processed_seq(last_processed_seq)

                yield doc
            except Exception as e:
                logging.warning(f"Error while processing incoming couchDB change: {e}")
                logging.debug(f"Data causing the error: {change}")


    def fetch_document_by_id(self, doc_id):
        """
        Fetches a document from the database by its ID.

        Args:
            doc_id (str): The ID of the document to fetch.

        Returns:
            dict: The retrieved document, or None if not found.
        """
        try:
            document = self.db[doc_id]
            return document
        except KeyError:
            logging.error(f'Document with ID {doc_id} not found in the database.')
            return None
        except Exception as e:
            logging.error(f'Error while accessing database: {e}')
            return None


class YggdrasilDBManager(CouchDBHandler):
    def __init__(self):
        super().__init__('yggdrasil')

    def create_project(self, project_id: str, projects_reference: str, method: str) -> YggdrasilDocument:
        new_document = YggdrasilDocument(
            project_id=project_id,
            projects_reference=projects_reference,
            method=method
        )
        self.save_document(new_document)
        logging.info(f"New project with ID {project_id} created successfully.")
        return new_document


    def save_document(self, document: YggdrasilDocument):
        try:
            self.db.save(document.to_dict())
            logging.info(f"Document with ID {document._id} saved successfully in 'yggdrasil' DB.")
        except Exception as e:
            logging.error(f"Error saving document: {e}")


    def get_document_by_project_id(self, project_id: str) -> Dict[str, Any]:
        try:
            document = self.db[project_id]
            return document
        except couchdb.http.ResourceNotFound:
            logging.info(f"Project with ID {project_id} not found.")
            return None
        except Exception as e:
            logging.error(f"Error while accessing project status: {e}")
            return None


    def update_sample_status(self, project_id: str, sample_id: str, status: str):
        try:
            document = self.get_document_by_project_id(project_id)
            if document:
                ygg_doc = YggdrasilDocument(
                    project_id=document['project_id'],
                    projects_reference=document['projects_reference'],
                    method=document['method']
                )
                ygg_doc.samples = document['samples']
                ygg_doc.update_sample_status(sample_id, status)
                ygg_doc.check_project_completion()
                self.save_document(ygg_doc)
                logging.info(f"Updated status of sample {sample_id} in project {project_id} to {status}.")
            else:
                logging.error(f"Project with ID {project_id} not found.")
        except Exception as e:
            logging.error(f"Error while updating sample status: {e}")


    def check_project_exists(self, project_id: str) -> Optional[Dict[str, Any]]:
        existing_document = self.get_document_by_project_id(project_id)
        if existing_document:
            logging.info(f"Project with ID {project_id} exists.")
            return existing_document
        else:
            logging.info(f"Project with ID {project_id} does not exist.")
            return None
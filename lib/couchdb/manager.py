import os
import couchdb

from lib.utils.config_loader import ConfigLoader
from lib.utils.couch_utils import save_last_processed_seq, get_last_processed_seq, has_required_fields

from lib.utils.logging_utils import custom_logger

logging = custom_logger(__name__.split('.')[-1])

class CouchDBManager:
    def __init__(self, db_url=None, db_user=None, db_password=None):
        # Load defaults from configuration file or environment
        self.db_config = ConfigLoader().load_config("main.json").get("couchdb", {})
        self.db_url = db_url or self.db_config.get("url")
        self.db_user = db_user or os.getenv("COUCH_USER", self.db_config.get("default_user"))
        self.db_password = db_password or os.getenv("COUCH_PASS", self.db_config.get("default_password"))

        self.server = None
        self.db = None

        self.connect_server()


    def connect_server(self):
        """Establishes a connection to the CouchDB server."""
        try:
            server_url = f"http://{self.db_user}:{self.db_password}@{self.db_url}"
            self.server = couchdb.Server(server_url)
            version = self.server.version()
            logging.info(f"Connected to CouchDB server. Version: {version}")
        except Exception as e:
            logging.error(f"An error occurred while connecting to the CouchDB server: {e}")
            raise ConnectionError("Failed to connect to CouchDB server")


    def connect_to_db(self, db_name):
        """Connect to a specific database on the established CouchDB server."""
        if not self.server:
            logging.error("Server is not connected. Please connect to server first.")
            raise ConnectionError("Server not connected")
        
        try:
            self.db = self.server[db_name]
            logging.info(f"Connected to database: {db_name}")
        except couchdb.http.ResourceNotFound:
            logging.error(f"Database {db_name} does not exist.")
            raise ConnectionError(f"Database {db_name} does not exist")
        except Exception as e:
            logging.error(f"Failed to connect to database {db_name}: {e}")
            raise ConnectionError(f"Could not connect to database {db_name}")


class ProjectDBManager(CouchDBManager):
    def __init__(self, db_url=None, db_user=None, db_password=None):
        super().__init__(db_url=db_url, db_user=db_user, db_password=db_password)
        self.connect_to_db("projects")
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


class YggdrasilDBManager(CouchDBManager):
    def __init__(self, db_url=None, db_user=None, db_password=None):
        super().__init__(db_url=db_url, db_user=db_user, db_password=db_password)
        self.connect_to_db("yggdrasil")

    # Methods to update and check sample and project statuses
    def update_sample_status(self, sample_id, status):
        # Implementation to update sample status
        pass

    def check_project_status(self, project_id):
        # Implementation to check the overall project status
        pass

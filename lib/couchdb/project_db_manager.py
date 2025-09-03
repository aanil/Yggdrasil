import json
from collections.abc import AsyncGenerator
from typing import Any

from ibm_cloud_sdk_core.api_exception import ApiException

from lib.core_utils.common import YggdrasilUtilities as Ygg
from lib.core_utils.config_loader import ConfigLoader
from lib.core_utils.logging_utils import custom_logger
from lib.couchdb.couchdb_connection import CouchDBHandler

logging = custom_logger(__name__.split(".")[-1])


class ProjectDBManager(CouchDBHandler):
    """
    Manages interactions with the 'projects' database, such as:

      - Asynchronously fetching document changes (`fetch_changes` / `get_changes`).
      - Retrieving documents by ID.

    Inherits from `CouchDBHandler` to reuse the CouchDB connection.
    It is specialized for Yggdrasil needs (e.g., module registry lookups).
    """

    def __init__(self) -> None:
        super().__init__("projects")
        self.module_registry = ConfigLoader().load_config("module_registry.json")

    async def fetch_changes(self) -> AsyncGenerator[tuple[dict[str, Any], str], None]:
        """Fetches document changes from the database asynchronously.

        Yields:
            Tuple[Dict[str, Any], str]: A tuple containing the document and module location.
        """
        last_processed_seq: str | None = None

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
        self, last_processed_seq: str | None = None
    ) -> AsyncGenerator[dict[str, Any], None]:
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

        changes = self.connection_manager.server.post_changes_as_stream(
            db=self.db_name,
            feed="continuous",
            since=last_processed_seq,
            include_docs=False,
        ).get_result()

        for line in changes.iter_lines():
            if line:
                change = json.loads(line)
                try:
                    doc = self.fetch_document_by_id(change["id"])
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
            document = self.connection_manager.server.get_document(
                db=self.db_name, doc_id=doc_id
            ).get_result()
            return document
        except ApiException:
            logging.error(f"Document with ID '{doc_id}' not found in the database.")
            return None
        except Exception as e:
            logging.error(f"Error while accessing database: {e}")
            return None

import functools
from typing import Any, Callable, Dict, Optional

import couchdb

from lib.core_utils.logging_utils import custom_logger
from lib.couchdb.couchdb_connection import CouchDBHandler
from lib.couchdb.yggdrasil_document import YggdrasilDocument

logging = custom_logger(__name__.split(".")[-1])


def auto_load_and_save(method: Callable) -> Callable:
    """
    Decorator that:
      1. Fetches the YggdrasilDocument by project_id
      2. Calls the wrapped method with that doc
      3. Saves the doc afterwards
    """

    @functools.wraps(method)
    def wrapper(self, project_id: str, *args, **kwargs) -> Any:
        ygg_doc = self.get_document_by_project_id(project_id)
        if not ygg_doc:
            logging.error(f"Project '{project_id}' not found in Yggdrasil DB.")
            return None  # or raise an exception

        try:
            # Inject the doc into the method call
            result = method(self, ygg_doc, *args, **kwargs)
        except Exception as e:
            logging.error(f"Error in {method.__name__} for project {project_id}: {e}")
            return

        # Save the doc (assuming it was modified)
        self.save_document(ygg_doc)
        return result

    return wrapper


class YggdrasilDBManager(CouchDBHandler):
    """Manages interactions with the 'yggdrasil' database."""

    def __init__(self) -> None:
        super().__init__("yggdrasil")

    def create_project(
        self,
        project_id: str,
        projects_reference: str,
        project_name: str,
        method: str,
        user_info: Optional[Dict[str, Dict[str, Optional[str]]]] = None,
        sensitive: Optional[bool] = True,
    ) -> YggdrasilDocument:
        """Creates a new project document in the database.

        Args:
            project_id (str): The project ID.
            projects_reference (str): Reference to the original project document.
            project_name (str): The project name.
            method (str): The library construction method.
            user_info (Optional[Dict[str, Dict[str, str]]]): Nested dict of user info,
                e.g. {"owner": {"email": "...", "name": "..."}, ...}.
            sensitive (bool): True if data is sensitive. Defaults to True.

        Returns:
            YggdrasilDocument: The newly created project document.
        """
        new_document = YggdrasilDocument(
            project_id=project_id,
            projects_reference=projects_reference,
            project_name=project_name,
            method=method,
        )

        # If we have user info, populate it into new_document.user_info
        # TODO: Make sure the PI and the owner are always set | Either here or upon delivery
        if user_info:
            new_document.user_info = user_info

        # Set sensitive flag to True by default (better safe than sorry)
        new_document.delivery_info["sensitive"] = sensitive

        self.save_document(new_document)
        logging.info(f"New project with ID '{project_id}' created successfully.")
        return new_document

    def save_document(self, document: YggdrasilDocument) -> None:
        """
        Save a document to the CouchDB database. If the document already exists,
        it updates the existing document while preserving the revision (_rev) field
        to avoid update conflicts.
        Args:
            document (YggdrasilDocument): The document to be saved, which must have
                          an _id attribute and a to_dict() method.
        Raises:
            Exception: If there is an error during the save operation, an exception
                   is logged with the error message.
        """
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

    def get_document_by_project_id(
        self, project_id: str
    ) -> Optional[YggdrasilDocument]:
        """Retrieves a document by project ID.

        Args:
            project_id (str): The project ID to search for.

        Returns:
            Optional[YggdrasilDocument]: An Yggdrasil document if found, else None.
        """
        try:
            document = self.db[project_id]
            return YggdrasilDocument.from_dict(document)
        except couchdb.http.ResourceNotFound:
            logging.info(f"Project with ID '{project_id}' not found.")
            return None
        except Exception as e:
            logging.error(f"Error accessing project: {e}")
            return None

    def check_project_exists(self, project_id: str) -> bool:
        """Checks if a project exists in the database.

        Args:
            project_id (str): The project ID to check.

        Returns:
            bool: True if the project exists, otherwise False
        """
        existing_document = self.get_document_by_project_id(project_id)
        if existing_document:
            logging.info(f"Project with ID '{project_id}' exists.")
            # TODO: Return the document or just True?
            # return existing_document
            return True
        else:
            logging.info(f"Project with ID '{project_id}' does not exist.")
            return False

    # --------------------------------------
    # Convenience Methods for Yggdrasil DB
    # --------------------------------------

    @auto_load_and_save
    def add_sample(
        self, _doc_injected: YggdrasilDocument, sample_id: str, status: str = "pending"
    ):
        """
        IMPORTANT: This method is decorated by @auto_load_and_save,
        so you must call it like:

            add_sample(<project_id>, <sample_id>, <status>)

        The decorator will fetch the YggdrasilDocument and pass it here as '_doc_injected'.

        ---

        Adds a sample to a project.

        Args:
            _doc_injected (YggdrasilDocument): The Yggdrasil document (injected by the decorator).
            sample_id (str): The sample ID.
            status (str): The status of the sample. Defaults to "pending".
        """
        _doc_injected.add_sample(sample_id=sample_id, status=status)
        logging.info(f"Sample '{sample_id}' added with status '{status}'.")

    @auto_load_and_save
    def update_sample_status(
        self, _doc_injected: YggdrasilDocument, sample_id: str, status: str
    ) -> None:
        """
        IMPORTANT: This method is decorated by @auto_load_and_save,
        so you must call it like:

            update_sample_status(<project_id>, <sample_id>, <status>)

        The decorator will fetch the YggdrasilDocument and pass it here as '_doc_injected'.

        ---

        Updates the status of a sample within a project.

        Args:
            _doc_injected (YggdrasilDocument): The Yggdrasil document (injected by the decorator).
            sample_id (str): The sample ID.
            status (str): The new status for the sample.
        """
        _doc_injected.update_sample_status(sample_id=sample_id, status=status)
        logging.info(f"Sample '{sample_id}' status updated to '{status}'.")

    @auto_load_and_save
    def add_ngi_report_entry(
        self,
        _doc_injected: YggdrasilDocument,
        report_data: Dict[str, Any],
    ) -> bool:
        """
        IMPORTANT: This method is decorated by @auto_load_and_save,
        so you must call it like:

            add_ngi_report_entry(<project_id>, <report_data>)

        The decorator will fetch the YggdrasilDocument and pass it here as '_doc_injected'.

        ---

        Adds an NGI report entry to a project.

        Args:
            _doc_injected (YggdrasilDocument): The Yggdrasil document (injected by the decorator).
            report_data (Dict[str, Any]): The NGI report data.
        """
        if not _doc_injected.add_ngi_report_entry(report_data):
            logging.warning("NGI report entry failed to be added to the document.")
            return False
        logging.info("NGI report entry added to the document.")
        return True

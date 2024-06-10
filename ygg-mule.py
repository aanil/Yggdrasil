#!/usr/bin/env python
import asyncio
import argparse

from lib.utils.config_loader import ConfigLoader
from lib.utils.common import YggdrasilUtilities as Ygg
from lib.utils.logging_utils import configure_logging, custom_logger
from lib.utils.couch_utils import couch_login

# Configure logging
configure_logging(debug=True)
logging = custom_logger("Ygg-Mule")

def process_document(doc_id):
    """
    Processes a document by its ID. Fetches the document from the database,
    determines the appropriate module to load, and executes the module.

    Args:
        doc_id (str): The ID of the document to process.
    """
    document = fetch_document_from_db(doc_id)

    if not document:
        logging.error(f"Document with ID {doc_id} not found.")
        return

    # Determine the appropriate module to load
    module_loc = get_module_location(document)

    # Load and execute the module
    try:
        RealmClass = Ygg.load_realm_class(module_loc)
        if RealmClass:
            realm = RealmClass(document)
            if realm.proceed:
                asyncio.run(realm.process())
                logging.info("Processing complete.")
            else:
                logging.info(f"Skipping processing due to missing required information. {document.get('project_id')}")
        else:
            logging.warning(f"Failed to load module '{module_loc}'.")
    except Exception as e:
        logging.error(f"Error while processing document: {e}", exc_info=True)


def fetch_document_from_db(doc_id):
    """
    Fetches a document from the database by its ID using Yggdrasil's CouchDB utilities.

    Args:
        doc_id (str): The ID of the document to fetch.

    Returns:
        dict: The retrieved document, or None if not found.
    """
    try:
        couch = couch_login()
        database = couch['projects']
        document = database[doc_id]
        return document
    except KeyError:
        logging.error(f'Document with ID {doc_id} not found in the database.')
        return None
    except Exception as e:
        logging.error(f'Error while accessing database: {e}')
        return None


def get_module_location(document):
    """
    Retrieves the module location based on the library construction method from the document.

    Args:
        document (dict): The document containing details about the library construction method.

    Returns:
        str: The module location, or None if not found.
    """
    try:
        # Load the module registry configuration
        module_registry = ConfigLoader().load_config("module_registry.json")

        # Extract the library construction method from the document
        method = document['details']['library_construction_method']

        # Retrieve module configuration for the specified method
        module_config = module_registry.get(method)

        if module_config:
            # Return the module location
            return module_config["module"]
        else:
            logging.warning(f"No module configuration found for method '{method}'.")
            return None
    except KeyError as e:
        logging.error(f'Error accessing module location: {e}')
        return None
    except Exception as e:
        logging.error(f'Unexpected error: {e}')
        return None


def main():
    logging.info("Ygg-Mule: Standalone Module Executor for Yggdrasil")
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Ygg-Mule: Standalone Module Executor for Yggdrasil')
    parser.add_argument('doc_id', type=str, help='Document ID to process')

    # Parse arguments
    args = parser.parse_args()

    # Process the document
    process_document(args.doc_id)

if __name__ == "__main__":
    main()

#!/usr/bin/env python

import argparse
import asyncio

from lib.core_utils.common import YggdrasilUtilities as Ygg
from lib.core_utils.config_loader import ConfigLoader
from lib.core_utils.logging_utils import configure_logging, custom_logger
from lib.core_utils.ygg_mode import YggMode
from lib.couchdb.project_db_manager import ProjectDBManager
from lib.couchdb.yggdrasil_db_manager import YggdrasilDBManager
from lib.realms.delivery.deliver import DeliveryManager

# Configure logging
configure_logging(debug=True)
logging = custom_logger("Ygg-Mule")


async def launch_realm(realm):
    try:
        # await realm.launch()
        await realm.launch_template()
    except Exception as e:
        logging.error(f"Error in realm.launch(): {e}", exc_info=True)


def process_project_doc(doc_id):
    """Fetch a project doc from the ProjectDB by its doc_id,
    find which analysis module to load, and execute that module.

    Args:
        doc_id (str): The ID of the document to process.
    """
    # Initialize the database managers
    pdm = ProjectDBManager()
    ydm = YggdrasilDBManager()

    # Fetch the document from the project database
    document = pdm.fetch_document_by_id(doc_id)
    if not document:
        logging.error(f"Project document with ID {doc_id} not found in Project DB.")
        return

    project_id = document.get("project_id")

    # Determine the appropriate module to load
    module_loc = get_module_location(document)
    if not module_loc:
        logging.warning(f"No module found for document with ID {doc_id}.")
        return

    # Load and execute the module
    try:
        RealmClass = Ygg.load_realm_class(module_loc)
        if RealmClass:
            realm = RealmClass(document, ydm)
            if realm.proceed:
                asyncio.run(launch_realm(realm))
                logging.info("Processing complete.")
            else:
                logging.info(
                    f"Skipping processing due to missing required information for project: {project_id}"
                )
        else:
            logging.warning(f"Failed to load module '{module_loc}' for doc {doc_id}.")
    except Exception as e:
        logging.error(f"Error while processing project doc: {e}", exc_info=True)


def process_yggdrasil_doc(doc_id):
    """
    Fetch an Yggdrasil document by its doc_id
    and pass it to the DeliveryManager flow.

    Args:
        doc_id (str): The ID of the document to process.
    """
    # Initialize the database managers
    ydm = YggdrasilDBManager()

    # Fetch the document from the yggdrasil database
    document = ydm.get_document_by_project_id(doc_id)
    if not document:
        logging.error(f"Document with ID {doc_id} not found in Yggdrasil DB.")
        return

    # Load and execute the module
    try:
        deliv_realm = DeliveryManager(document, ydm)
        if deliv_realm.proceed:
            asyncio.run(launch_realm(deliv_realm))
            logging.info("Delivery processing complete.")
        else:
            logging.info(f"Skipping delivery: Not enough info in doc {doc_id}.")
    except Exception as e:
        logging.error(f"Error while processing yggdrasil doc: {e}", exc_info=True)


# TODO: If the module registry doesn’t change often, consider caching it to avoid reloading it every time
def get_module_location(document):
    """Retrieve the module location based on the library construction method.

    Args:
        document (dict): The document containing details about the library construction method.

    Returns:
        str or None: The module location if found; otherwise, None.
    """
    try:
        # Load the module registry configuration
        module_registry = ConfigLoader().load_config("module_registry.json")

        # Extract the library construction method from the document
        method = document["details"]["library_construction_method"]

        # Retrieve module configuration for the specified method
        # module_config = module_registry.get(method)
        # if module_config:
        #     return module_config["module"]

        # Direct match
        if method in module_registry:
            return module_registry[method]["module"]

        # If no exact match, check for prefix matches
        for registered_method, config in module_registry.items():
            if config.get("prefix") and method.startswith(registered_method):
                return config["module"]

        logging.warning(f"No module configuration found for method '{method}'.")
        return None
    except KeyError as e:
        logging.error(f"Error accessing module location: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        return None


def main():
    """Main function to parse arguments and start Yggdrasil."""
    logging.info("Ygg-Mule: Standalone Module Executor for Yggdrasil")

    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Ygg-Mule: Standalone Module Executor for Yggdrasil"
    )
    parser.add_argument("doc_id", type=str, help="Document ID to process")
    parser.add_argument(
        "-d",
        "--delivery",
        action="store_true",
        help="Indicate if this is a delivery document in Yggdrasil DB.",
    )

    parser.add_argument("--dev", action="store_true", help="Enable development mode")

    # Parse arguments
    args = parser.parse_args()

    # Set dev mode (if enabled)
    YggMode.init(args.dev)

    # Process the document
    if args.delivery:
        process_yggdrasil_doc(args.doc_id)
    else:
        process_project_doc(args.doc_id)


if __name__ == "__main__":
    main()

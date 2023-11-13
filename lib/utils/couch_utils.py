import couchdb
import logging

from lib.utils.common import YggdrasilUtilities as Ygg
from lib.utils.config_loader import config_manager as cm
# from lib.utils.config_utils import get_env_variable, load_json_config
# from lib.utils.config_utils import get_config_file_path


def couch_login():
    """
    Log in to a CouchDB server and return a CouchDB server connection.

    This function logins to the CouchDB server URL and returns a connection to it.

    Returns:
        couchdb.Server: A connection to the CouchDB server.
    """
    # config = load_json_config()
    couchdb_url = cm["couchdb_url"]

    # Get credentials and login to CouchDB
    couchdb_username = Ygg.env_variable("COUCH_USER")
    couchdb_password = Ygg.env_variable("COUCH_PASS")

    logging.info(couchdb_username)

    # TODO: It seems the couchdb.client.login authentication is not working. Explore this further.
    server_url = f"http://{couchdb_username}:{couchdb_password}@{couchdb_url}"

    server = couchdb.Server(server_url)
    logging.info(server_url)

    return server


def get_last_processed_seq():
    """
    Retrieve the last processed sequence number from a file.
    Returns:
        str: The last processed sequence number.
    """
    # Get the last couchdb sequence file path
    seq_file = Ygg.get_path(".last_processed_seq")

    if seq_file.is_file():
        with open(seq_file, "r") as file:
            return file.read().strip()
    else:
        # If the file doesn't exist, return a default value.
        default_since = '68007-g1AAAACheJzLYWBgYMpgTmEQTM4vTc5ISXIwNDLXMwBCwxyQVCJDUv3___-zMpiTGBjKG3KBYuxpKWaJBgaG2PTgMSmPBUgyNACp_3ADJ6mDDTQwTDYzsDTDpjULACnTKcM'
        return default_since


def save_last_processed_seq(last_processed_seq):
    """
    Save the last processed sequence number to a file.
    Args:
        last_processed_seq (str): The last processed sequence number to save.
    """
    # Get the last couchdb sequence file path
    seq_file = Ygg.get_path(".last_processed_seq")

    with open(seq_file, "w") as file:
        file.write(last_processed_seq)


def has_required_fields(doc, required_fields):
    """
    Check if a CouchDB document contains all the required fields.

    Args:
        doc (dict): The CouchDB document to be validated.
        required_fields (list): A list of field names to be checked in the document.

    Returns:
        bool: True if the document contains all the required fields; False otherwise.
    """
    for req_field in required_fields:
        field_names = req_field.split('.')

        current = doc

        for field_name in field_names:
            if field_name in current:
                current = current[field_name]
            else:
                logging.info(f"Field name '{field_name}' not in Document")
                return False
    return True



# TODO: Try using the 'longpoll' feed type instead of 'continuous'.
# TODO: "last_seq" exists into the returned results. Save "last_seq" after analyzing every change.
async def get_db_changes(db, last_processed_seq=None):
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

    # Use the Changes API to continuously monitor document changes in the database.
    changes = db.changes(feed='continuous', include_docs=False, since=last_processed_seq)

    # Iterate through the changes and yield documents matching the criteria.
    for change in changes:
        try:
            doc = db.get(change['id'])
            last_processed_seq = change['seq']
            save_last_processed_seq(last_processed_seq)

            yield doc
        except Exception as e:
            logging.warning(f"Error while processing incoming couchDB change: {e}")
            logging.error(f"Data causing the error: {change}")
            # pass
        # yield change['doc']

            # try:
            #     # Filter by 'library_construction_method'
            #     # TODO: Remember to remove the hardcoded project_ids
            #     if (change['doc']['project_id'] in ['P27408', 'P27459']) or (change['doc']['details']['library_construction_method'] == 'SmartSeq 3'):  # (change['doc']['project_id'] == 'P27408')
            #         yield change['doc']
            # except KeyError as e:
            #     # Handle cases where the expected structure is not present in the document.
            #     # Generally we want to skip these documents, so pass.
            #     pass
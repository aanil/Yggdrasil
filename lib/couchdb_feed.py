import logging

from lib.utils.config_loader import ConfigLoader
from lib.utils.couch_utils import get_db_changes, couch_login
# from lib.utils.config_utils import get_module_registry
# from lib.branches.ss3_branch.smartseq3 import smartseq3

# Function to interact with CouchDB
async def fetch_data_from_couchdb():
    """
    Fetch data from CouchDB based on the provided configuration.

    Returns:
        dict: Retrieved data from CouchDB.
    """

    # TODO: Avoid relogging in if already logged in
    couch = couch_login()

    # Set only if you want to start from a specific sequence
    last_processed_seq = None
    # last_processed_seq = '68007-g1AAAACheJzLYWBgYMpgTmEQTM4vTc5ISXIwNDLXMwBCwxyQVCJDUv3___-zMpiTGBjKG3KBYuxpKWaJBgaG2PTgMSmPBUgyNACp_3ADJ6mDDTQwTDYzsDTDpjULACnTKcM'
    last_processed_seq = '72679-g1AAAACheJzLYWBgYMpgTmEQTM4vTc5ISXIwNDLXMwBCwxyQVCJDUv3___-zMpiTGBgak3OBYuxpKWaJBgaG2PTgMSmPBUgyNACp_3ADZ7WADTQwTDYzsDTDpjULAC7GKhU'

    module_registry = ConfigLoader().load_config("module_registry.json")

    while True:
        async for change in get_db_changes(couch['projects'], last_processed_seq=last_processed_seq):
            try:
                method = change['details']['library_construction_method']
                
                module_config = module_registry[method]

                if module_config:
                    module_loc = module_config["module"]
                    options = module_config.get("options", {})

                    yield (change, module_loc, options)

                else:
                    # The majority of the tasks will not have a module configured.
                    # If you log this, expect to see many messages!
                    # logging.warning(f"No module configured for task type '{method}'.")
                    pass
            except Exception as e:
                    # logging.warning(f"Error while processing incoming couchDB data: {e}")
                    # logging.error(f"Data causing the error: {data}")
                    pass




### OLD CODE ###
'''
    while True:
        for change in get_db_changes(couch['projects'], last_processed_seq=last_processed_seq):
            method = change['details']['library_construction_method']
            if method == 'SmartSeq 3':
                #required_fields = ss3_fields
                modules[method].smartseq3(change)
            pass
'''
import logging

from lib.utils.config_utils import load_json_config
#from lib.branches._10x.utils import has_required_fields

def process(doc):
    """
    Process 10x task based on the CouchDB change document.

    Args:
        change: The CouchDB change document for the task.
    """
    # Implement SmartSeq 3-specific logic here
    logging.info("Here we are! 10x")
    _10x_config = load_json_config("10x_config.json", "lib/branches/_10x/")

    # if has_required_fields(doc, ss3_config["required_fields"]):
    #     logging.info("Has required fields!")
    #     pass
import logging

from lib.branches._10x import gex
from lib.branches._10x import atac
from lib.branches._10x import vdj
from lib.branches._10x import multiome


#from lib.branches._10x.utils import has_required_fields

def process(doc):
    """
    Process 10x task based on the CouchDB change document.

    Args:
        change: The CouchDB change document for the task.
    """

    try:
        print(doc['details']['library_prep_option'])
        if doc['details']['library_prep_option']:
            prep_option = doc['details']['library_prep_option']

            if prep_option == "Chromium: 3' GEX":
                gex.process(doc)
            elif prep_option == "Chromium: ATAC-seq":
                atac.process(doc)
            elif prep_option == "Chromium: VDJ":
                vdj.process(doc)
            elif prep_option == "Chromium: Multiome":
                multiome.process(doc)
            else:
                logging.warning(f"No module configured for task type '{prep_option}'.")
                pass

    except Exception as e:
        logging.warning(f"Error while processing incoming couchDB data: {e}")
        # print(doc['details'])
    # prep_option = doc['details']

    # if doc['details']['customer_project_reference'] == 'ESCG-BH-212':
    #     print(doc)

    # if has_required_fields(doc, ss3_config["required_fields"]):
    #     logging.info("Has required fields!")
    #     pass
#!/usr/bin/env python
import asyncio
import logging

from lib.utils.common import YggdrasilUtilities as Ygg
from lib.utils.config_loader import configs as ygg_configs
from lib.utils.logging_utils import configure_logging
from lib.couchdb_feed import fetch_data_from_couchdb


#Call configure_logging to set up the logging environment
configure_logging(debug=True)


# Define asynchronous functions for task handling
async def process_couchdb_changes():
    while True:
        try:
            # Fetch data from CouchDB and call the appropriate module
            async for data, module_loc, module_options in fetch_data_from_couchdb():
                try:
                    # Dynamically load the module
                    module = Ygg.load_module(module_loc)

                    if module:
                        # Call the module's process function
                        module.process(data)
                    else:
                        logging.warning(f"Failed to load module '{module_loc}' for '{data['details']['library_construction_method']}'.")
                except Exception as e:
                    logging.warning(f"Error while trying to load module: {e}")
                    # logging.error(f"Data causing the error: {data}")


            # If an HPC job is required, submit it asynchronously
            # await submit_hpc_job(data)
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            # logging.error(f"Data causing the error: {data}")

        # Sleep to avoid excessive polling
        print("Sleeping...")
        await asyncio.sleep(ygg_configs["couchdb_poll_interval"])


# Define asynchronous function for monitoring and post-processing HPC jobs
async def monitor_hpc_jobs():
    while True:
        # Monitor and process completed HPC jobs
        # If a job is completed, handle the post-processing and data delivery

        # Sleep to avoid excessive polling
        await asyncio.sleep(ygg_configs["job_monitor_poll_interval"])


# Main daemon loop
async def main():
    """
    Main daemon loop.
    """
    # config = load_json_config()

    # Start the asynchronous coroutine for processing CouchDB changes
    couchdb_task = process_couchdb_changes()

    # Start the asynchronous coroutine for monitoring HPC jobs
    job_monitor_task = monitor_hpc_jobs()

    tasks = asyncio.all_tasks()
    for task in tasks:
        print(f"> {task.get_name()}, {task.get_coro()}")

    # Wait for both tasks to complete
    await asyncio.gather(couchdb_task, job_monitor_task)

if __name__ == "__main__":
    asyncio.run(main())

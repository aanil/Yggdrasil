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
    tasks = []
    while True:
        try:
            # Fetch data from CouchDB and call the appropriate module
            async for data, module_loc, module_options in fetch_data_from_couchdb():
                try:
                    # Dynamically load the module
                    # module = Ygg.load_module(module_loc)
                    print(f"Module location: {module_loc}")
                    RealmClass = Ygg.load_realm_class(module_loc)

                    if RealmClass:
                        # Call the module's process function
                        realm = RealmClass(data)
                        if realm.proceed:
                            task = asyncio.create_task(realm.process())
                            tasks.append(task)
                            print(f"Tasks ({realm.project_info['project_id']}): {tasks}")
                            # module.process(data)
                        else:
                            logging.info(f"Skipping task creation due to missing required information. {data.get('project_id')}")
                    else:
                        logging.warning(f"Failed to load module '{module_loc}' for '{data['details']['library_construction_method']}'.")
                except Exception as e:
                    logging.warning(f"Error while trying to load module: {e}", exc_info=True)
                    logging.error(f"Data causing the error: {data}")

                # Limit the number of concurrent tasks if necessary
                # TODO: move to using ygg_configs["tasks_limit"] or similar
                tasks_limit = 2
                if len(tasks) >= tasks_limit:
                    # Wait for all tasks to complete
                    await asyncio.gather(*tasks)
                    tasks = []

                # Sleep to avoid excessive polling
                print("Sleeping in async for loop...")
                await asyncio.sleep(ygg_configs["couchdb_poll_interval"])

            # If an HPC job is required, submit it asynchronously
            # await submit_hpc_job(data)
        except Exception as e:
            logging.error(f"An error occurred: {e}", exc_info=True)
            # logging.error(f"Data causing the error: {data}")

        # After the loop, wait for any remaining tasks to complete
        if tasks:
            await asyncio.gather(*tasks)
            tasks = []

        # Sleep to avoid excessive polling
        print("Sleeping in while loop...")
        await asyncio.sleep(ygg_configs["couchdb_poll_interval"])


# Main daemon loop
async def main():
    """
    Main daemon loop.
    """
    # config = load_json_config()

    # Start the asynchronous coroutine for processing CouchDB changes
    couchdb_task = process_couchdb_changes()

    tasks = asyncio.all_tasks()
    for task in tasks:
        print(f"> {task.get_name()}, {task.get_coro()}")

    # Wait for both tasks to complete
    await asyncio.gather(couchdb_task)

if __name__ == "__main__":
    asyncio.run(main())

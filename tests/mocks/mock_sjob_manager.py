import asyncio
import random
import string

from lib.core_utils.logging_utils import custom_logger
from lib.module_utils.sjob_manager import SlurmJobManager

logging = custom_logger(__name__.split(".")[-1])


class MockSlurmJobManager(SlurmJobManager):
    def __init__(self, polling_interval=1.0, command_timeout=8.0):
        self.polling_interval = polling_interval
        self.command_timeout = command_timeout
        self.jobs = {}  # Keep track of mock jobs

    async def submit_job(self, script_path):
        mock_job_id = "".join(random.choices(string.digits, k=4))
        self.jobs[mock_job_id] = "PENDING"
        # Simulate a delay before the job starts
        asyncio.create_task(self._start_job(mock_job_id))
        return mock_job_id

    # async def monitor_job(self, job_id, callback=None):
    #     while self.jobs.get(job_id) != "COMPLETED":
    #         await asyncio.sleep(self.polling_interval)
    #     logging.info(f"Job {job_id} status: COMPLETED")
    #     if callback:
    #         callback(job_id, "COMPLETED")

    async def monitor_job(self, job_id, sample):
        while self.jobs.get(job_id) != "COMPLETED":
            await asyncio.sleep(self.polling_interval)
        # logging.info(f"Job {job_id} status: COMPLETED")
        self.check_status(job_id, "COMPLETED", sample)

    async def _start_job(self, job_id):
        # Simulate a random wait time between 15 and 35 seconds
        wait_time = random.uniform(15, 35)
        await asyncio.sleep(wait_time)
        self.jobs[job_id] = "COMPLETED"

    # ... other methods as needed ...

    @staticmethod
    def check_status(job_id, status, sample):
        """
        Checks the status of a job and calls the appropriate method on the sample object.

        Args:
            job_id (str): The job ID.
            status (str): The status of the job.
            sample (object): The sample object (must have a post_process method and id attribute).
        """
        logging.debug(f"Job {job_id} status: {status}")
        if status == "COMPLETED":
            logging.info(f"Sample {sample.id} processing completed.")
            sample.post_process()
            sample.status = "completed"
        elif status in ["FAILED", "CANCELLED"]:
            sample.status = "failed"
            logging.info(f"Sample {sample.id} processing failed.")

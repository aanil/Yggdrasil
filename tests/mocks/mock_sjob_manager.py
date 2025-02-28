import asyncio
import random
import string

from lib.core_utils.logging_utils import custom_logger

logging = custom_logger(__name__.split(".")[-1])


class MockSlurmJobManager:

    slurm_end_states = [
        "COMPLETED",
        "FAILED",
        "CANCELLED",
        "CANCELLED+",
        "TIMEOUT",
        "OUT_OF_ME+",
    ]

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
        logging.info(
            f"Monitoring job {job_id} with poll interval {self.polling_interval}..."
        )
        while True:
            state = await self._job_status(job_id)
            if state in self.slurm_end_states:
                break
            await asyncio.sleep(self.polling_interval)
        # logging.info(f"Job {job_id} status: COMPLETED")
        # self.check_status(job_id, "COMPLETED", sample)
        self.check_status_new(job_id, state, sample)

    async def _start_job(self, job_id):
        # Simulate a random wait time between 5 and 10 seconds
        wait_time = random.uniform(5, 10)
        await asyncio.sleep(wait_time)
        self.jobs[job_id] = "COMPLETED"
        logging.info(f"Mock job {job_id} done. Updated to COMPLETED.")

    async def _job_status(self, job_id: str) -> str:
        if job_id not in self.jobs:
            logging.info(
                f"Detected unknown job {job_id}. Marking as PROCESSING and scheduling completion."
            )
            self.jobs[job_id] = "PROCESSING"
            asyncio.create_task(self._start_job(job_id))
        return self.jobs[job_id]

    @staticmethod
    def check_status(job_id, status, sample):
        """
        Checks the status of a job and calls the appropriate method on the sample object.

        Args:
            job_id (str): The job ID.
            status (str): The status of the job.
            sample (object): The sample object (must have a post_process method and id attribute).
        """
        logging.info("\n")
        logging.debug(f"[{sample.id}] Job {job_id} status: {status}")
        if status == "COMPLETED":
            logging.info(f"[{sample.id}] Job completed successfully.")
            sample.status = "processed"
            sample.post_process()
            # sample.status = "completed"
        elif status in ["FAILED", "CANCELLED", "TIMEOUT", "OUT_OF_ME+"]:
            sample.status = "processing_failed"
            logging.info(f"[{sample.id}] Job failed.")
        else:
            logging.warning(f"[{sample.id}] Job ended with unexpacted status: {status}")
            sample.status = "processing_failed"

    @staticmethod
    def check_status_new(job_id, status, sample):
        """
        Checks the status of a job and calls the appropriate method on the sample object.

        Args:
            job_id (str): The job ID.
            status (str): The status of the job.
            sample (object): The sample object (must have a post_process method and id attribute).
        """
        logging.info("\n")
        logging.debug(f"[{sample.id}] Job {job_id} status: {status}")
        if status == "COMPLETED":
            logging.info(f"[{sample.id}] Job completed successfully.")
            sample.status = "processed"
            # sample.status = "completed"
        elif status in ["FAILED", "CANCELLED", "CANCELLED+", "TIMEOUT", "OUT_OF_ME+"]:
            sample.status = "processing_failed"
            logging.info(f"[{sample.id}] Job failed.")
        else:
            logging.warning(f"[{sample.id}] Job ended with unexpacted status: {status}")
            sample.status = "processing_failed"

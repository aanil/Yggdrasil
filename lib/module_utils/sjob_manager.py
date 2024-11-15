import asyncio
import re
import subprocess
from pathlib import Path
from typing import Any, Optional, Union

from lib.core_utils.config_loader import configs
from lib.core_utils.logging_utils import custom_logger

logging = custom_logger(__name__.split(".")[-1])

# import asyncio
# import logging
# import re

# from pathlib import Path

# from lib.utils.config_loader import configs

# class SlurmJobManager:
#     def __init__(self, polling_interval=1.0, command_timeout=8.0):
#         self.polling_interval = polling_interval
#         self.command_timeout = command_timeout

#         # TODO: Make sure the path to the slurm_manager.sh script exists or log an error
#         self.slurm_script_path = Path(configs['yggdrasil_script_dir']) / "slurm_manager.sh"  # Adjust this path as necessary

#     async def submit_job(self, script_path):
#         command = [self.slurm_script_path, "submit", script_path]

#         print(">>>> COMMAND: ", command)
#         try:
#             process = await asyncio.create_subprocess_exec(
#                 *command,
#                 stdout=asyncio.subprocess.PIPE,
#                 stderr=asyncio.subprocess.PIPE
#             )
#             stdout, stderr = await asyncio.wait_for(process.communicate(), self.command_timeout)

#             if process.returncode != 0:
#                 logging.error("Error submitting job. STDOUT: %s, STDERR: %s", stdout.decode(), stderr.decode())
#                 return None

#             logging.debug(f"Slurm RAW submit output: {stdout}")
#             logging.debug(f"STDOUT from slurm_manager.sh: {stdout.decode().strip()}")
#             logging.debug(f"STDERR from slurm_manager.sh: {stderr.decode().strip()}")
#             stdout_decoded = stdout.decode().strip()
#             logging.debug(f"Slurm submit output: {stdout_decoded}")

#             # Improved regex to capture the job ID from a string like "Submitted batch job 123456"
#             match = re.search(r'Submitted batch job (\d+)', stdout_decoded)
#             job_id = match.group(1) if match else None

#             if job_id:
#                 logging.info(f"Job submitted with ID: {job_id}")
#                 return job_id
#             else:
#                 logging.error("Failed to extract job ID from sbatch output.")

#         except asyncio.TimeoutError:
#             logging.error("Timeout while submitting job.")
#         except Exception as e:
#             logging.error(f"Unexpected error: {e}")

#         return None

#     async def monitor_job(self, job_id, sample):
#         """Monitors the specified job and calls the sample's post-process method based on job status."""
#         while True:
#             status = await self._job_status(job_id)
#             print(f">>>> RECEIVED STATUS: {status}")
#             if status in ["COMPLETED", "FAILED", "CANCELLED"]:
#                 logging.info(f"Job {job_id} status: {status}")
#                 self.check_status(job_id, status, sample)
#                 break
#             await asyncio.sleep(self.polling_interval)

#     async def _job_status(self, job_id):
#         command = [self.slurm_script_path, "monitor", job_id]
#         try:
#             process = await asyncio.create_subprocess_exec(
#                 *command,
#                 stdout=asyncio.subprocess.PIPE,
#                 stderr=asyncio.subprocess.PIPE
#             )
#             stdout, stderr = await asyncio.wait_for(process.communicate(), self.command_timeout)

#             if process.returncode == 0:
#                 return stdout.decode().strip()

#         except asyncio.TimeoutError:
#             logging.error(f"Timeout while checking status of job {job_id}.")
#         except Exception as e:
#             logging.error(f"Unexpected error while checking status of job {job_id}: {e}")

#         return None

#     @staticmethod
#     def check_status(job_id, status, sample):
#         """
#         Checks the status of a job and calls the appropriate method on the sample object.

#         Args:
#             job_id (str): The job ID.
#             status (str): The status of the job.
#             sample (object): The sample object (must have a post_process method and id attribute).
#         """
#         print(f"Job {job_id} status: {status}")
#         if status == "COMPLETED":
#             print(f"Sample {sample.id} processing completed.")
#             sample.post_process()
#             sample.status = "completed"
#         elif status in ["FAILED", "CANCELLED"]:
#             sample.status = "failed"
#             print(f"Sample {sample.id} processing failed.")


#################################################################################################
######### CLASS BELOW ASSUMES ACCESS TO THE HOST SYSTEM TO SUBMIT SLURM JOBS ####################
#################################################################################################


class SlurmJobManager:
    """Manages the submission and monitoring of Slurm jobs.

    Attributes:
        polling_interval (float): Interval for polling job status in seconds.
        command_timeout (float): Timeout for Slurm commands in seconds.
    """

    def __init__(
        self, polling_interval: float = 10.0, command_timeout: float = 8.0
    ) -> None:
        """Initialize the SlurmJobManager with specified polling interval and command timeout.

        Args:
            polling_interval (float, optional): Interval for polling job status in seconds.
                Defaults to 10.0 seconds.
            command_timeout (float, optional): Timeout for Slurm commands in seconds.
                Defaults to 8.0 seconds.
        """
        self.polling_interval: float = configs.get(
            "job_monitor_poll_interval", polling_interval
        )
        self.command_timeout: float = command_timeout

    async def submit_job(self, script_path: Union[str, Path]) -> Optional[str]:
        """Submit a Slurm job using the specified script.

        Args:
            script_path (Union[str, Path]): Path to the Slurm script.

        Returns:
            Optional[str]: The job ID if submission is successful, None otherwise.
        """
        sbatch_command = ["sbatch", str(script_path)]

        if not Path(script_path).is_file():
            logging.error(f"Script file does not exist: {script_path}")
            return None

        try:
            process = await asyncio.create_subprocess_exec(
                *sbatch_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), self.command_timeout
            )

            if process.returncode != 0:
                logging.error(f"Error submitting job. Details: {stderr.decode()}")
                return None

            match = re.search(r"\d+", stdout.decode())
            job_id = match.group() if match else None

            # NOTE: Improved logic in case it's needed in the future
            # stdout_decoded = stdout.decode().strip()
            # match = re.search(r"Submitted batch job (\d+)", stdout_decoded)
            # job_id = match.group(1) if match else None

            if job_id:
                logging.info(f"Job submitted with ID: {job_id}")
                return job_id
            else:
                logging.error(
                    f"Failed to parse job ID from sbatch output: {stdout.decode().strip()}"
                )
        except asyncio.TimeoutError:
            logging.error("Timeout while submitting job.")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")

        return None

    async def monitor_job(self, job_id: str, sample: Any) -> None:
        """Monitor the specified job and handle its status accordingly.

        Continuously checks the status of a Slurm job until it completes or fails.
        Depending on the final status, it calls the `check_status` method to handle the sample.

        Args:
            job_id (str): The job ID.
            sample (Any): The sample object with `id` attribute.
        """
        logging.debug(f"[{sample.id}] Job {job_id} submitted for monitoring.")
        while True:
            status = await self._job_status(job_id)
            if status in ["COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "OUT_OF_ME+"]:
                # logging.info(f"Job {job_id} status: {status}")
                self.check_status(job_id, status, sample)
                break
            await asyncio.sleep(self.polling_interval)

    async def _job_status(self, job_id: str) -> Optional[str]:
        """Retrieve the status of a Slurm job.

        Args:
            job_id (str): The job ID.

        Returns:
            Optional[str]: The status of the job, or None if unable to retrieve.
        """
        sacct_command = f"sacct -n -X -o State -j {job_id}"
        try:
            process = await asyncio.create_subprocess_shell(
                sacct_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if stderr:
                logging.error(f"sacct stderr: {stderr.decode().strip()}")

            if stdout:
                stdout_decoded = stdout.decode().strip()
                logging.debug(f"sacct stdout for job {job_id}: {stdout_decoded}")
                return stdout_decoded
        except asyncio.TimeoutError:
            logging.error(f"Timeout while checking status of job {job_id}.")
        except Exception as e:
            logging.error(
                f"Unexpected error while checking status of job {job_id}: {e}"
            )

        return None

    @staticmethod
    def check_status(job_id: str, status: str, sample: Any) -> None:
        """Check the status of a job and update the sample accordingly.

        Args:
            job_id (str): The job ID.
            status (str): The status of the job.
            sample (object): The sample object with `id` and `status` attributes.
        """
        logging.debug(f"Job {job_id} status: {status}")
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

import re
import asyncio
import subprocess
import logging

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
    def __init__(self, polling_interval=1.0, command_timeout=8.0):
        self.polling_interval = polling_interval
        self.command_timeout = command_timeout

    async def submit_job(self, script_path):
        sbatch_command = ["sbatch", script_path]
        try:
            result = await asyncio.create_subprocess_exec(
                *sbatch_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(result.communicate(), self.command_timeout)

            if result.returncode != 0:
                logging.error("Error submitting job. Details: %s", stderr.decode())
                return None

            match = re.search(r'\d+', stdout.decode())
            job_id = match.group() if match else None

            if job_id:
                logging.info(f"Job submitted with ID: {job_id}")
                return job_id

        except asyncio.TimeoutError:
            logging.error("Timeout while submitting job.")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")

        return None

    # async def monitor_job(self, job_id, callback=None):
    #     while True:
    #         status = await self._job_status(job_id)
    #         if status in ["COMPLETED", "FAILED", "CANCELLED"]:
    #             logging.info(f"Job {job_id} status: {status}")
    #             if callback:
    #                 callback(job_id, status)
    #             break
    #         await asyncio.sleep(self.polling_interval)

    async def monitor_job(self, job_id, sample):
        """Monitors the specified job and calls the sample's post-process method based on job status."""
        while True:
            status = await self._job_status(job_id)
            print(f">>>> RECEIVED MONITORING STATUS: {status}")
            if status in ["COMPLETED", "FAILED", "CANCELLED"]:
                logging.info(f"Job {job_id} status: {status}")
                self.check_status(job_id, status, sample)
                break
            await asyncio.sleep(self.polling_interval)

    async def _job_status(self, job_id):
        print(f"Checking status of job {job_id}")
        sacct_command = f"sacct -n -X -o State -j {job_id}"
        try:
            process = await asyncio.create_subprocess_shell(
                sacct_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), self.command_timeout)

            if stderr:
                logging.error(f"Error from sacct command: {stderr.decode()}")

            if process.returncode == 0 and stdout:
                status_output = stdout.decode().strip()
                logging.debug(f"sacct output for job {job_id}: {status_output}")
                return stdout.decode().strip()

        except asyncio.TimeoutError:
            logging.error(f"Timeout while checking status of job {job_id}.")
        except Exception as e:
            logging.error(f"Unexpected error while checking status of job {job_id}: {e}")

        return None
    
    @staticmethod
    def check_status(job_id, status, sample):
        """
        Checks the status of a job and calls the appropriate method on the sample object.

        Args:
            job_id (str): The job ID.
            status (str): The status of the job.
            sample (object): The sample object (must have a post_process method and id attribute).
        """
        print(f"Job {job_id} status: {status}")
        if status == "COMPLETED":
            print(f"Sample {sample.id} processing completed.")
            sample.post_process()
            sample.status = "completed"
        elif status in ["FAILED", "CANCELLED"]:
            sample.status = "failed"
            print(f"Sample {sample.id} processing failed.")
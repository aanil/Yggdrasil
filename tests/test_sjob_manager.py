import asyncio
import subprocess
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from lib.module_utils.sjob_manager import SlurmJobManager


class MockSample:
    def __init__(self, id):
        self.id = id

    def post_process(self):
        pass  # Add your mock implementation here if needed


class TestSlurmJobManager(unittest.TestCase):
    def setUp(self):
        self.manager = SlurmJobManager()
        self.sample = MagicMock()
        self.sample.id = "sample1"
        self.sample.post_process = AsyncMock()

    async def test_monitor_job(self):
        with unittest.mock.patch.object(
            self.manager, "_job_status", new_callable=AsyncMock
        ) as mock_job_status, unittest.mock.patch.object(
            self.manager, "check_status"
        ) as mock_check_status:

            for status in ["COMPLETED", "FAILED", "CANCELLED"]:
                mock_job_status.return_value = status
                await self.manager.monitor_job("job1", self.sample)
                mock_check_status.assert_called_with("job1", status, self.sample)

    @patch(
        "lib.utils.sjob_manager.asyncio.create_subprocess_exec", new_callable=AsyncMock
    )
    @patch("lib.utils.sjob_manager.asyncio.wait_for", new_callable=AsyncMock)
    def test_submit_job(self, mock_wait_for, mock_create_subprocess_exec):
        # Set up the mocks
        mock_create_subprocess_exec.return_value.communicate.return_value = (
            b"1234",
            b"",
        )
        mock_create_subprocess_exec.return_value.returncode = 0
        mock_wait_for.return_value = (b"1234", b"")

        # Call the submit_job method
        job_id = asyncio.run(self.manager.submit_job("script.sh"))

        # Assert the mocks were called correctly
        mock_create_subprocess_exec.assert_called_once_with(
            "sbatch", "script.sh", stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        mock_wait_for.assert_called_once()

        # Assert the correct job ID was returned
        self.assertEqual(job_id, "1234")

    @patch(
        "lib.utils.sjob_manager.asyncio.create_subprocess_shell", new_callable=AsyncMock
    )
    @patch("lib.utils.sjob_manager.asyncio.wait_for", new_callable=AsyncMock)
    def test__job_status(self, mock_wait_for, mock_create_subprocess_shell):
        # Set up the mocks
        mock_create_subprocess_shell.return_value.communicate.return_value = (
            b"COMPLETED",
            b"",
        )
        mock_create_subprocess_shell.return_value.returncode = 0
        mock_wait_for.return_value = (b"COMPLETED", b"")

        # Call the _job_status method
        status = asyncio.run(self.manager._job_status("1234"))

        # Assert the mocks were called correctly
        mock_create_subprocess_shell.assert_called_once_with(
            "sacct -n -X -o State -j 1234",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        mock_wait_for.assert_called_once()

        # Assert the correct status was returned
        self.assertEqual(status, "COMPLETED")


if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from ygg_trunk import process_couchdb_changes


class TestProcessCouchDBChanges(unittest.IsolatedAsyncioTestCase):

    @patch("ygg_trunk.fetch_data_from_couchdb", new_callable=AsyncMock)
    @patch("ygg_trunk.Ygg.load_realm_class")
    @patch("ygg_trunk.asyncio.create_task")
    @patch("ygg_trunk.asyncio.gather", new_callable=AsyncMock)
    @patch("ygg_trunk.asyncio.sleep", new_callable=AsyncMock)
    @patch("ygg_trunk.logging")
    async def test_process_couchdb_changes(
        self,
        mock_logging,
        mock_sleep,
        mock_gather,
        mock_create_task,
        mock_load_realm_class,
        mock_fetch_data,
    ):
        # Mock the dependencies
        mock_fetch_data.return_value.__aiter__.return_value = iter(
            [(MagicMock(), "module_loc", "module_options")]
        )
        mock_load_realm_class.return_value = MagicMock(
            proceed=True, process=AsyncMock()
        )
        mock_create_task.return_value = "task"

        # Make asyncio.sleep raise an exception after being called once
        mock_sleep.side_effect = [None, Exception("Stop loop")]

        with self.assertRaises(Exception, msg="Stop loop"):
            # Call the function
            await process_couchdb_changes()

        # Assert the expected behavior
        mock_fetch_data.assert_called_once()
        mock_load_realm_class.assert_called_once_with("module_loc")
        mock_create_task.assert_called_once()
        mock_gather.assert_called_once_with("task")
        mock_sleep.assert_called()

        # Assert no errors were logged
        mock_logging.error.assert_not_called()
        mock_logging.warning.assert_not_called()


if __name__ == "__main__":
    unittest.main()

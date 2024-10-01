import unittest
import asyncio

from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from lib.core_utils.couch_utils import couch_login, get_db_changes, save_last_processed_seq, get_last_processed_seq, has_required_fields

class TestCouchUtils(unittest.TestCase):

    def test_save_last_processed_seq(self):
        # Test that the last processed sequence number is saved correctly
        # This will require mocking the file write operation
        with unittest.mock.patch('builtins.open', unittest.mock.mock_open()) as mock_file:
            save_last_processed_seq('12345')
            mock_file().write.assert_called_once_with('12345')

    def test_get_last_processed_seq(self):
        # Mock the file read operation
        mock_open_instance = mock_open(read_data='12345')
        with patch('builtins.open', mock_open_instance):
            # Call the function
            seq = get_last_processed_seq()
            # Assert the function returned the correct sequence number
            self.assertEqual(seq, '12345')

    def test_has_required_fields(self):
        # Test that the function correctly identifies when a document has all required fields
        doc = {'field1': 'value1', 'field2': 'value2'}
        required_fields = ['field1', 'field2']
        self.assertTrue(has_required_fields(doc, required_fields))

        # Test that the function correctly identifies when a document is missing a required field
        doc = {'field1': 'value1'}
        required_fields = ['field1', 'field2']
        self.assertFalse(has_required_fields(doc, required_fields))

    @patch('lib.utils.couch_utils.Ygg')
    @patch('lib.utils.couch_utils.couchdb.Server')
    def test_couch_login(self, mock_server, mock_ygg):
        # Mock the environment variables
        mock_ygg.env_variable.side_effect = ['username', 'password']
        # Mock the server instance
        mock_server_instance = MagicMock()
        mock_server.return_value = mock_server_instance
        # Call the function
        server = couch_login()
        # Assert the server instance was called with the correct URL
        mock_server.assert_called_once_with('http://username:password@ngi-statusdb-dev.scilifelab.se:5984')
        # Assert the function returned the server instance
        self.assertEqual(server, mock_server_instance)

    @patch('lib.utils.couch_utils.couch_login')
    def test_get_db_changes(self, mock_couch_login):
        # Mock the CouchDB server and database
        mock_couch = MagicMock()
        mock_db = MagicMock()
        mock_db.changes = MagicMock()  # Mock the 'changes' method
        mock_couch.__getitem__.return_value = mock_db
        mock_couch_login.return_value = mock_couch

        # Call the function and get the generator
        changes_generator = get_db_changes(mock_couch['projects'])

        # Define an async function to iterate over the generator
        async def iterate_over_generator():
            async for _ in changes_generator:
                pass
        # Run the async function
        asyncio.run(iterate_over_generator())
        # Assert the database's changes feed was accessed
        mock_db.changes.assert_called_once()

if __name__ == '__main__':
    unittest.main()
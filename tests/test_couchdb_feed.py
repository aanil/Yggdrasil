# import unittest
# from unittest.mock import MagicMock, patch

# from lib.couchdb_feed import fetch_data_from_couchdb

# class TestCouchDBFeed(unittest.TestCase):

#     @patch('lib.couchdb_feed.get_db_changes')
#     @patch('lib.couchdb_feed.couch_login')
#     async def test_fetch_data_from_couchdb(self, mock_couch_login, mock_get_db_changes):
#         # Mock the dependencies
#         mock_couch_login.return_value = {'projects': 'mock_db'}
#         mock_get_db_changes.return_value = [
#             {'details': {'library_construction_method': 'SmartSeq 3'}, 'change': 'change1'},
#             {'details': {'library_construction_method': 'Other'}, 'change': 'change2'}
#         ]

#         # Call the function
#         result = await fetch_data_from_couchdb()

#         # Assert the expected behavior
#         self.assertEqual(result, None)  # Replace with your expected result

#         # Assert the dependencies were called with the correct arguments
#         mock_couch_login.assert_called_once()
#         mock_get_db_changes.assert_called_once_with('mock_db', last_processed_seq=None)

# if __name__ == '__main__':
#     unittest.main()

import unittest
from unittest.mock import MagicMock, patch
from trashcan.couchdb_feed import fetch_data_from_couchdb

class TestCouchDBFeed(unittest.TestCase):

    @patch('lib.couchdb_feed.get_db_changes')
    @patch('lib.couchdb_feed.couch_login')
    @patch('lib.couchdb_feed.ConfigLoader')
    async def test_fetch_data_from_couchdb(self, mock_ConfigLoader, mock_couch_login, mock_get_db_changes):
        # Mock the dependencies
        mock_couch_login.return_value = {'projects': 'mock_db'}
        mock_get_db_changes.return_value = iter([{'details': {'library_construction_method': 'SmartSeq 3'}, 'seq': 'seq1'}])
        mock_ConfigLoader.return_value.load_config.return_value = {'SmartSeq 3': {'module': 'module1'}}

        # Call the function
        result = await fetch_data_from_couchdb()

        # Assert the expected behavior
        # TODO: Replace with your expected result
        self.assertEqual(result, None)

        # Assert the dependencies were called with the correct arguments
        mock_couch_login.assert_called_once()
        mock_get_db_changes.assert_called_once_with('mock_db', last_processed_seq='72679-g1AAAACheJzLYWBgYMpgTmEQTM4vTc5ISXIwNDLXMwBCwxyQVCJDUv3___-zMpiTGBgak3OBYuxpKWaJBgaG2PTgMSmPBUgyNACp_3ADZ7WADTQwTDYzsDTDpjULAC7GKhU')
        mock_ConfigLoader.assert_called_once()
        mock_ConfigLoader.return_value.load_config.assert_called_once_with("module_registry.json")

if __name__ == '__main__':
    unittest.main()
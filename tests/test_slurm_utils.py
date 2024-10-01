
import unittest
from unittest.mock import mock_open, patch
from lib.core_utils.slurm_utils import generate_slurm_script

class TestGenerateSlurmScript(unittest.TestCase):
    def test_generate_slurm_script(self):
        # Define the input arguments
        args_dict = {
            "job_name": "test_batch",
            "yaml_filepath": "/home/user/path/to.yaml",
        }
        template_fpath = "slurm_template.sh"
        output_fpath = "slurm_script.sh"
        template_content = "{job_name}\n{yaml_filepath}\n"
        expected_script_content = "test_batch\n/home/user/path/to.yaml\n"

        # Patch the 'open' function and mock its behavior
        with patch("builtins.open", mock_open(read_data=template_content)) as mock_file:
            # Call the function under test
            generate_slurm_script(args_dict, template_fpath, output_fpath)
            
            # Assert that the 'open' function was called with the correct arguments
            mock_file.assert_any_call(template_fpath, "r")
            mock_file.assert_any_call(output_fpath, "w")
            
            # Assert that the 'write' method of the file object was called with the expected content
            mock_file().write.assert_called_once_with(expected_script_content)

if __name__ == '__main__':
    unittest.main()

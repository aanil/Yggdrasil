import subprocess

from lib.core_utils.config_loader import configs
from lib.core_utils.logging_utils import custom_logger

logging = custom_logger(__name__)

def generate_ngi_report(project_path, project_id, user_name, sample_list):
    """
    Generates an NGI report for a specified project using external reporting tools.

    Args:
        project_path (str): Path to the project directory where the report will be generated.
        project_id (str): Unique identifier for the project.
        user_name (str): Name of the user generating the report.
        sample_list (list): A list of sample identifiers to be included in the report.

    Returns:
        bool: True if the report was generated successfully, False otherwise.
    """
    # Convert list of samples into a space-separated string for the command line
    samples_str = ' '.join(sample_list)
    
    # Command to activate the environment and run the NGI report generation
    activate_env_cmd = configs.get('activate_ngi_cmd', None)
    if not activate_env_cmd:
        logging.error("NGI environment activation command not found in the configuration. NGI report will not be generated.")
        return False
    report_cmd = f"ngi_reports project_summary -d {project_path} -p {project_id} -s '{user_name}' -y --no_txt --samples {samples_str}"
    full_cmd = f"{activate_env_cmd} && {report_cmd}"
    
    try:
        # Execute the combined command
        process = subprocess.run(full_cmd, shell=True, text=True, capture_output=True)
        
        # Check the outcome of the subprocess
        if process.returncode == 0:
            logging.info("NGI report generated successfully.")
            return True
        else:
            # Log the error message if the command failed
            logging.error(f"Failed to generate NGI report: {process.stderr.strip()}")
            return False
    except Exception as e:
        # Log any unexpected exceptions during the execution
        logging.exception(f"An error occurred while generating the NGI report: {str(e)}")
        return False


# generate_ngi_report('/home/anastasios/Documents/git/Yggdrasil/yggdrasil_workspace/workflows/smartseq3/projects/I__Adameyko_23_02', 'P28510', 'Name Surname', ['P28510_2001', 'P28510_2002', 'P28510_2003'])

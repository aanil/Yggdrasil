import glob

from pathlib import Path

from lib.utils.logging_utils import custom_logger

logging = custom_logger(__name__.split('.')[-1])

class SampleFileHandler:
    """
    Handles file operations for a 10x sample, including managing file paths, creating necessary directories,
    locating reference and FASTQ files, creating symlinks, validating output files, etc.

    Attributes:
        sample_id (str): Identifier for the sample.]
        flowcell_ids (list): List of associated flowcells.
        project_id (str): Identifier for the project.
        project_name (str): Name of the project.
        sample_ref (str): Reference genome for the sample.
        config (dict): Configuration settings.
        base_dir (Path): Base directory path for the project.
        sample_dir (Path): Directory path for the sample.
        fastq_files_dir (Path): Directory path for FASTQ files.
        fastq_files (dict): Dictionary of FASTQ file paths.
    """

    # TODO: Only pass the project_name if project_info is not used anywhere else
    def __init__(self, sample):
        """
        Initialize the SampleFileHandler with sample information and configuration settings.

        Args:
            sample (object): The sample object containing sample data and project information.
        """
        self.sample_id = sample.run_sample_id
        self.project_id = sample.project_info.get('project_id', None)
        self.project_name = sample.project_info.get('project_name', None) # TODO: Remove this if not used anywhere else / see todo above
        self.sample_ref = sample.project_info.get('ref_genome', None)
        self.organism = sample.project_info.get('organism', None)
        self.config = sample.config

        # Define sample folder structure
        self.base_dir = Path(self.config['10x_dir']) / self.project_name
        self.sample_dir = self.base_dir / self.sample_id
        self.fastq_files_dir = self.base_dir / 'fastq_files'

        self.fastq_files = {}

        # Define critical file paths
        self.init_file_paths()


    def init_file_paths(self):
        # Files needed for processing
        self.slurm_script_path = self.base_dir / f"{self.sample_id}_slurm_script.sh"

        # Report output files
        self.summary_fpath = self.sample_dir / 'outs' / 'web_summary.html'

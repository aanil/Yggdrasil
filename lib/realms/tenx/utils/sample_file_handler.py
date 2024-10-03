from pathlib import Path
from typing import Any, Dict, Optional

from lib.core_utils.logging_utils import custom_logger

logging = custom_logger(__name__.split(".")[-1])


class SampleFileHandler:
    """
    Handles file operations for a 10x sample, including managing file paths,
    creating necessary directories, locating reference and FASTQ files,
    creating symlinks, validating output files, etc.

    Attributes:
        sample_id (str): Identifier for the sample.]
        project_id (str): Identifier for the project.
        project_name (str): Name of the project.
        sample_ref (str): Reference genome for the sample.
        organism (str): Organism associated with the sample.
        config (Dict[str, Any]): Configuration settings.
        base_dir (Path): Base directory path for the project.
        sample_dir (Path): Directory path for the sample.
        fastq_files_dir (Path): Directory path for FASTQ files.
        fastq_files (Dict[str, Any]): Dictionary of FASTQ file paths.
        slurm_script_path (Path): Path to the SLURM script file.
        summary_fpath (Path): Path to the summary output file.
    """

    def __init__(self, sample: Any) -> None:
        """Initialize the SampleFileHandler with sample information and configuration settings.

        Args:
            sample (Any): The sample object containing sample data and project information.
        """
        self.sample_id: str = sample.run_sample_id
        self.project_id: Optional[str] = sample.project_info.get("project_id")
        self.project_name: Optional[str] = sample.project_info.get("project_name")
        self.sample_ref: Optional[str] = sample.project_info.get("ref_genome")
        self.organism: Optional[str] = sample.project_info.get("organism")
        self.config: Dict[str, Any] = sample.config

        # Define sample folder structure
        self.base_dir: Path = Path(self.config["10x_dir"]) / self.project_name
        self.sample_dir: Path = self.base_dir / self.sample_id
        self.fastq_files_dir: Path = self.base_dir / "fastq_files"

        self.fastq_files: Dict[str, Any] = {}

        # Define critical file paths
        self.init_file_paths()

    def init_file_paths(self) -> None:
        """Initialize critical file paths."""
        # Files needed for processing
        self.slurm_script_path = self.base_dir / f"{self.sample_id}_slurm_script.sh"

        # Report output files
        # NOTE: Different pipelines may produce summaries in different locations
        self.summary_fpath = self.sample_dir / "outs" / "web_summary.html"

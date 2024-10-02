
from abc import ABC, abstractmethod
from typing import Any

from lib.module_utils.sjob_manager import SlurmJobManager

class AbstractProject(ABC):
    """Abstract base class for realm module projects in the Yggdrasil application.

    The `AbstractProject` serves as a foundational framework for the diverse realms connected by Yggdrasil.
    Each realm (processing module) extends this template, defining its unique processing logic while adhering
    to the core structure laid out by this class.

    This template outlines the common steps and sequences, while allowing flexibility for specific realm implementations. 
    It ensures that while each realm follows its own internal rules, they are all integral parts of Yggdrasil's tree
    structure, contributing to the overarching narrative and functionality of the application.

    Attributes:
        sjob_manager (SlurmJobManager): Manages submission and monitoring of Slurm jobs.
        doc (Any): The document representing the project or data to be processed.
        yggdrasil_db_manager (Any): The database manager for Yggdrasil-specific database operations.
    """

    def __init__(self, doc: Any, yggdrasil_db_manager: Any) -> None:
        """Initialize the AbstractProject.

        Args:
            doc (Any): The document representing the project (data to be processed).
            yggdrasil_db_manager (Any): The database manager for Yggdrasil-specific database operations.
        """
        self.sjob_manager: SlurmJobManager  = SlurmJobManager()
        self.doc: Any = doc
        self.yggdrasil_db_manager: Any = yggdrasil_db_manager

    @abstractmethod
    def pre_process(self) -> None:
        """Handle preliminary processing specific to the realm's requirements."""
        pass

    @abstractmethod
    async def process(self) -> None:
        """Define the main processing logic for the project.

        This method should be implemented by each project class to define how the processing
        of the document unfolds.

        Note:
            Since processing might involve asynchronous operations (e.g., submitting and monitoring jobs),
            this method is defined as asynchronous.
        """
        pass

    @abstractmethod
    def create_slurm_job(self, data: Any) -> str:
        """Create a Slurm job for the given data.

        Args:
            data (Any): The data to create a Slurm job for.

        Returns:
            str: The path to the created Slurm job script.
        """
        pass

    def submit_job(self, script: str) -> Any:
        """Submit a job to the Slurm scheduler using the SlurmJobManager.

        Args:
            script_path (str): The path to the script or command to be submitted as a job.

        Returns:
            Any: The job ID or submission result.
        """
        return self.sjob_manager.submit_job(script)

    def monitor_job(self, job_id: str) -> Any:
        """Monitor the status of a submitted Slurm job using the SlurmJobManager.

        Args:
            job_id (str): The identifier of the submitted job to be monitored.

        Returns:
            Any: The result of the job monitoring.
        """
        return self.sjob_manager.monitor_job(job_id)

    @abstractmethod
    def post_process(self, result: Any) -> None:
        """Handle post-processing specific to the project's outcome.

        Args:
            result (Any): The result from the Slurm job to be post-processed.
        """
        pass


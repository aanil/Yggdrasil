from abc import ABC, abstractmethod
from typing import Any

from lib.core_utils.logging_utils import custom_logger
from lib.module_utils.sjob_manager import SlurmJobManager

logging = custom_logger(__name__.split(".")[-1])


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
        ydm (Any): The database manager (yggdrasil_db_manager) for Yggdrasil-specific database operations.
    """

    def __init__(self, doc: Any, yggdrasil_db_manager: Any) -> None:
        """Initialize the AbstractProject.

        Args:
            doc (Any): The document representing the project (data to be processed).
            yggdrasil_db_manager (Any): The database manager for Yggdrasil-specific database operations.
        """
        self.sjob_manager: SlurmJobManager = SlurmJobManager()
        self.doc: Any = doc
        self.ydm: Any = yggdrasil_db_manager
        self.project_id: str = self.doc.get("project_id")
        self.doc_id: str = self.doc.get("_id")
        self.method: str = self.doc.get("details", {}).get(
            "library_construction_method", ""
        )
        self.user_info: dict = {
            "owner": {
                "email": self.doc.get("order_details", {})
                .get("owner", {})
                .get("email", ""),
                "name": self.doc.get("order_details", {})
                .get("owner", {})
                .get("name", ""),
            },
            "bioinformatician": {
                "email": self.doc.get("order_details", {})
                .get("fields", {})
                .get("project_bx_email", ""),
                "name": self.doc.get("order_details", {})
                .get("fields", {})
                .get("project_bx_name", ""),
            },
            "pi": {
                "email": self.doc.get("order_details", {})
                .get("fields", {})
                .get("project_pi_email", ""),
                "name": self.doc.get("order_details", {})
                .get("fields", {})
                .get("project_pi_name", ""),
            },
            "lab": {
                "name": self.doc.get("order_details", {})
                .get("fields", {})
                .get("project_lab_email", ""),
                "email": self.doc.get("order_details", {})
                .get("fields", {})
                .get("project_lab_name", ""),
            },
        }
        sensitive_str = self.doc.get("details", {}).get("sensitive_data", "").lower()
        self.is_sensitive = sensitive_str == "yes"

        self.status: str = "ongoing"
        self.project_info: dict = {}
        self.samples: list = []
        self.proceed: bool = False  # Default to False; subclasses can override

    # def setup_project(self):
    #     """Template method defining the steps for project setup."""
    #     self.proceed = self.check_required_fields()
    #     if self.proceed:
    #         self.initialize_project_in_db()
    #         # self._extract_project_specific_info()
    #         # self.extract_samples()
    #     else:
    #         logging.error("Cannot proceed due to missing required fields.")

    def initialize_project_in_db(self):
        """Initialize the project in the Yggdrasil database."""
        existing_document = self.ydm.check_project_exists(self.project_id)
        if not existing_document:
            # Create the project in YggdrasilDB
            self.ydm.create_project(
                self.project_id,
                self.doc_id,
                self.method,
                self.user_info,
                self.is_sensitive,
            )
            logging.info(f"Project {self.project_id} created in YggdrasilDB.")
        else:
            logging.info(f"Project {self.project_id} already exists in YggdrasilDB.")
            document = self.ydm.get_document_by_project_id(self.project_id)
            if document:
                self.status = document.project_status
                if self.status == "completed":
                    logging.info(
                        f"Project with ID {self.project_id} is already completed. Skipping processing."
                    )
                    self.proceed = False
                else:
                    logging.info(
                        f"Project with ID {self.project_id} has status '{self.status}' and will be processed."
                    )
                    self.proceed = True
                    # Update/sync the project in YggdrasilDB
                    document.sync_project_metadata(
                        user_info=self.user_info,
                        is_sensitive=self.is_sensitive,
                    )
                    self.ydm.save_document(document)
            else:
                logging.error(
                    f"Could not fetch YggdrasilDocument for {self.project_id}."
                )
                self.proceed = False

    def add_samples_to_project_in_db(self):
        """Add samples to the project in the Yggdrasil database."""
        for sample in self.samples:
            self.ydm.add_sample(
                project_id=self.project_id,
                sample_id=sample.id,
                # lib_prep_option=sample.project_info.get("library_prep_option", ""),
                status=sample.status,
            )

    @abstractmethod
    def check_required_fields(self) -> bool:
        """Check if the document contains all required fields.

        Returns:
            bool: True if all required fields are present, False otherwise.
        """
        pass

    @abstractmethod
    async def launch(self) -> None:
        """Define the main processing logic for the project.

        This method should be implemented by each project class to define how the processing
        of the document unfolds.

        Note:
            Since its course might involve asynchronous operations (e.g., submitting and monitoring jobs),
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

    def monitor_job(self, job_id: str, sample: Any) -> Any:
        """Monitor the status of a submitted Slurm job using the SlurmJobManager.

        Args:
            job_id (str): The identifier of the submitted job to be monitored.
            sample (Any): The sample object associated with the job.

        Returns:
            Any: The result of the job monitoring.
        """
        return self.sjob_manager.monitor_job(job_id, sample)

    @abstractmethod
    def post_process(self, result: Any) -> None:
        """Handle post-processing specific to the project's outcome.

        Args:
            result (Any): The result from the Slurm job to be post-processed.
        """
        pass

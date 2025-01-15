import datetime
from typing import Any, Dict, List, Optional

from lib.core_utils.logging_utils import custom_logger

logging = custom_logger(__name__.split(".")[-1])


class YggdrasilDocument:
    """Represents a Yggdrasil project document.

    Attributes:
        _id (str): The unique identifier of the project (same as project_id).
        projects_reference (str): Reference to the original project document.
        method (str): The library construction method.
        project_id (str): The project ID.
        status (str): The current status of the project.
        start_date (str): ISO formatted start date and time.
        end_date (str): ISO formatted end date and time.
        samples (List[Dict[str, Any]]): List of samples associated with the project.
    """

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "YggdrasilDocument":
        """Creates a YggdrasilDocument instance from a dictionary.

        Args:
            data (Dict[str, Any]): The dictionary containing document data.

        Returns:
            YggdrasilDocument: The created instance.
        """
        instance = cls(
            project_id=data.get("project_id", ""),
            projects_reference=data.get("projects_reference", ""),
            method=data.get("method", ""),
        )
        instance.status = data.get("status", "ongoing")
        instance.start_date = data.get(
            "start_date", datetime.datetime.now().isoformat()
        )
        instance.end_date = data.get("end_date", "")
        instance.samples = data.get("samples", [])
        instance.delivery_info = data.get("delivery_info", {})
        return instance

    def __init__(self, project_id: str, projects_reference: str, method: str) -> None:
        """Initializes a new YggdrasilDocument instance.

        Args:
            project_id (str): The project ID.
            projects_reference (str): Reference to the original project document.
            method (str): The library construction method.
        """
        self._id: str = project_id
        self.projects_reference: str = projects_reference
        self.method: str = method
        self.project_id: str = project_id
        self.status: str = "ongoing"
        self.start_date: str = datetime.datetime.now().isoformat()
        self.end_date: str = ""
        self.samples: List[Dict[str, Any]] = []
        self.delivery_info: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        """Converts the YggdrasilDocument to a dictionary.

        Returns:
            Dict[str, Any]: A dictionary representation of the document.
        """
        return {
            "_id": self._id,
            "projects_reference": self.projects_reference,
            "method": self.method,
            "project_id": self.project_id,
            "status": self.status,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "samples": self.samples,
            "delivery_info": self.delivery_info,
        }

    def add_sample(
        self,
        sample_id: str,
        # lib_prep_option: str,
        status: str = "pending",
        flowcell_ids_processed_for: Optional[List[str]] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> None:
        """Adds a new sample to the document.

        Args:
            sample_id (str): The sample ID.
            lib_prep_option (str): The library preparation option.
            status (str, optional): The status of the sample. Defaults to "pending".
            flowcell_ids_processed_for (List[str], optional): Flowcell IDs the sample has been processed for.
            start_time (str, optional): Start time of the sample processing.
            end_time (str, optional): End time of the sample processing.
        """
        existing_sample = self.get_sample(sample_id)
        if existing_sample:
            # Update existing sample
            existing_sample["status"] = status
            if flowcell_ids_processed_for:
                existing_sample["flowcell_ids_processed_for"].extend(
                    flowcell_ids_processed_for
                )
                # Remove duplicates
                existing_sample["flowcell_ids_processed_for"] = list(
                    set(existing_sample["flowcell_ids_processed_for"])
                )
            if start_time:
                existing_sample["start_time"] = start_time
            if end_time:
                existing_sample["end_time"] = end_time
            # logging.debug(f"Updated sample: {existing_sample}")
        else:
            # Add new sample
            sample = {
                "sample_id": sample_id,
                "status": status,
                # "lib_prep_option": lib_prep_option,
                "start_time": start_time or "",
                "end_time": end_time or "",
                "flowcell_ids_processed_for": flowcell_ids_processed_for or [],
                # "QC": ""
            }
            self.samples.append(sample)
            # logging.debug(f"Added sample: {sample}")

    def update_sample_status(self, sample_id: str, status: str) -> None:
        """Updates the status of a specific sample.

        Args:
            sample_id (str): The sample ID to update.
            status (str): The new status of the sample.
        """
        sample = self.get_sample(sample_id)
        if sample:
            sample["status"] = status
            current_time = datetime.datetime.now().isoformat()
            if status in ["processing", "running"]:
                sample["start_time"] = current_time
            elif status in [
                "completed",
                "processing_failed",
                "post_processing_failed",
                "aborted",
            ]:
                sample["end_time"] = current_time
        else:
            logging.error(
                f"Sample with ID '{sample_id}' not "
                f"found in project '{self.project_id}'."
            )

        # Check if the project status needs to be updated
        self.check_project_completion()

    def get_sample(self, sample_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a specific sample from the samples list by its ID.

        Args:
            sample_id (str): The sample ID to retrieve.

        Returns:
            Optional[Dict[str, Any]]: The sample dictionary if found, else None.
        """
        for sample in self.samples:
            if sample["sample_id"] == sample_id:
                return sample
        return None

    def update_project_status(self, status: str) -> None:
        """Updates the status of the project.

        Args:
            status (str): The new status of the project.
        """
        self.status = status
        if status == "completed":
            if not self.end_date:
                self.end_date = datetime.datetime.now().isoformat()
        elif status in ["processing", "failed"]:
            self.end_date = ""

    def check_project_completion(self) -> None:
        """
        Determines the project status based on its samples.

        Logic:
            1) If any sample is active (e.g. 'processing', 'running', etc.),
            project -> 'processing'
            2) Else if every sample is finished ('completed' or 'aborted'),
            project -> 'completed'
            3) Else if every sample is not_yet_started ('pending', 'unsequenced', etc.),
            project -> 'pending'
            4) Otherwise, project -> 'partially_completed'
        """
        # You may adjust these sets to match your real usage
        active_statuses = {
            "initialized",
            "processing",
            "pre_processing",
            "post_processing",
            "requires_manual_submission",
        }
        finished_statuses = {"completed", "aborted"}
        not_yet_started_statuses = {"pending", "unsequenced"}

        # Collect all sample statuses into a set for quick membership checks
        sample_statuses = [sample["status"] for sample in self.samples]
        unique_statuses = set(sample_statuses)

        # 1) If any sample is "active" => project is 'processing'
        if any(status in active_statuses for status in unique_statuses):
            self.status = "processing"
            self.end_date = ""  # not fully completed
            return

        # 2) If ALL samples are "finished" => 'completed'
        if all(status in finished_statuses for status in unique_statuses):
            self.status = "completed"
            if not self.end_date:
                self.end_date = datetime.datetime.now().isoformat()
            return

        # 3) If ALL samples are "not_yet_started" => 'pending'
        if all(status in not_yet_started_statuses for status in unique_statuses):
            self.status = "pending"
            self.end_date = ""
            return

        # 4) Otherwise => 'partially_completed'
        # means no sample is actively running, but at least one is neither finished nor not_yet_started
        self.status = "partially_completed"
        self.end_date = ""

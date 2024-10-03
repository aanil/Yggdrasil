import datetime
from typing import Any, Dict, List, Optional


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
        }

    def add_sample(
        self, sample_id: str, lib_prep_option: str, status: str = "pending"
    ) -> None:
        """Adds a new sample to the document.

        Args:
            sample_id (str): The sample ID.
            lib_prep_option (str): The library preparation option.
            status (str, optional): The status of the sample. Defaults to "pending".
        """
        sample = {
            "sample_id": sample_id,
            "status": status,
            "lib_prep_option": lib_prep_option,
            "start_time": "",
            "end_time": "",
            "flowcell_ids_processed_for": [],
        }
        self.samples.append(sample)

    def update_sample_status(self, sample_id: str, status: str) -> None:
        """Updates the status of a specific sample.

        Args:
            sample_id (str): The sample ID to update.
            status (str): The new status of the sample.
        """
        for sample in self.samples:
            if sample["sample_id"] == sample_id:
                sample["status"] = status
                if status == "running":
                    sample["start_time"] = datetime.datetime.now().isoformat()
                elif status in ["completed", "failed"]:
                    sample["end_time"] = datetime.datetime.now().isoformat()
                break

        # Check if the project status needs to be updated
        self.check_project_completion()

    def get_sample(self, sample_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a specific sample by its ID.

        Args:
            sample_id (str): The sample ID to retrieve.

        Returns:
            Optional[Dict[str, Any]]: The sample dictionary if found, else None.
        """
        for sample in self.samples:
            if sample["sample_id"] == sample_id:
                return sample
        return None

    def check_project_completion(self) -> None:
        """Checks if all samples are completed and updates the project status.

        Samples with status "completed" or "aborted" are considered completed.

        Note:
            There will be cases where samples are "aborted". These samples
            should be considered as "completed" for the project status.
        """
        # if all(sample["status"] == "completed" for sample in self.samples):
        if all(sample["status"] in ["completed", "aborted"] for sample in self.samples):
            self.status = "completed"
            self.end_date = datetime.datetime.now().isoformat()
        else:
            # If any sample is not completed (or aborted), set the project status to ongoing
            self.status = "ongoing"
            # Clear the end date since the project is not completed
            self.end_date = ""

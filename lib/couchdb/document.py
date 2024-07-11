import datetime
from typing import List, Dict, Any

class YggdrasilDocument:
    def __init__(self, project_id: str, projects_reference: str, method: str):
        self._id = project_id
        self.projects_reference = projects_reference
        self.method = method
        self.project_id = project_id
        self.status = "ongoing"
        self.start_date = datetime.datetime.now().isoformat()
        self.end_date = ""
        self.samples = []

    def to_dict(self) -> Dict[str, Any]:
        # Convert the document to a dictionary
        return {
            "_id": self._id,
            "projects_reference": self.projects_reference,
            "method": self.method,
            "project_id": self.project_id,
            "status": self.status,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "samples": self.samples
        }

    def add_sample(self, sample_id: str, lib_prep_option: str, status: str = "pending"):
        # Add a new sample to the document
        sample = {
            "sample_id": sample_id,
            "status": status,
            "lib_prep_option": lib_prep_option,
            "start_time": "",
            "end_time": "",
            "flowcell_ids_processed_for": []
        }
        self.samples.append(sample)

    def update_sample_status(self, sample_id: str, status: str):
        # Update the status of a specific sample
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


    def get_sample(self, sample_id: str) -> Dict[str, Any]:
        # Retrieve a specific sample by its ID
        for sample in self.samples:
            if sample["sample_id"] == sample_id:
                return sample
        return {}


    def check_project_completion(self):
        # Check if all samples are completed and update the project status
        if all(sample["status"] == "completed" for sample in self.samples):
            self.status = "completed"
            self.end_date = datetime.datetime.now().isoformat()
        else:
            self.status = "ongoing"  # If any sample is not completed, set the project status to ongoing
            self.end_date = ""  # Clear the end date since the project is not completed


import asyncio
from pathlib import Path
from typing import List

from lib.base.abstract_project import AbstractProject
from lib.core_utils.config_loader import ConfigLoader
from lib.core_utils.logging_utils import custom_logger

# from datetime import datetime
from lib.module_utils.ngi_report_generator import generate_ngi_report
from lib.realms.smartseq3.ss3_sample import SS3Sample

logging = custom_logger("SS3 Project")


class SmartSeq3(AbstractProject):
    """
    Class representing a SmartSeq3 project.

    Attributes:
        config (MappingProxyType): Configuration settings for the SmartSeq3 project.
        doc (dict): Document containing project data.
        proceed (bool): Flag indicating whether the project has all required fields to proceed.
        project_info (dict): Extracted project information.
        project_dir (Path): Path to the project directory.
        samples (list): List of SS3Sample instances.
    """

    config = ConfigLoader().load_config("ss3_config.json")

    def __init__(self, doc, yggdrasil_db_manager):
        """
        Initialize a SmartSeq3 project instance.

        Args:
            doc (dict): Document containing project metadata.
        """
        super().__init__(doc, yggdrasil_db_manager)
        self.proceed = self.check_required_fields()

        if self.proceed:
            self.initialize_project_in_db()
            self.project_info = self._extract_project_info()
            self.project_dir = self.ensure_project_directory()
            self.project_info["project_dir"] = self.project_dir

    def check_required_fields(self):
        """
        Checks if the document contains all required fields.

        Returns:
            bool: True if all required fields are present, False otherwise.
        """
        required_fields = self.config.get("required_fields", [])
        sample_required_fields = self.config.get("sample_required_fields", [])

        missing_keys = [
            field for field in required_fields if not self._is_field(field, self.doc)
        ]

        if missing_keys:
            logging.warning(f"Missing required project information: {missing_keys}.")
            return False

        # Check sample-specific required fields
        samples = self.doc.get("samples", {})
        for sample_id, sample_data in samples.items():
            for field in sample_required_fields:
                if not self._is_field(field, sample_data):
                    logging.warning(
                        f"Missing required sample information '{field}' in sample '{sample_id}'."
                    )

                    if "total_reads_(m)" in field:
                        # TODO: Send this message as a notification on Slack
                        logging.warning("Consider running 'Aggregate Reads' in LIMS.")
                    return False
        return True

    def _is_field(self, field_path, data):
        """
        Checks if the document contains all required fields.

        Returns:
            bool: True if all required fields are present, False otherwise.
        """
        keys = field_path.split(".")
        for key in keys:
            if isinstance(data, dict) and key in data:
                data = data[key]
            else:
                return False
        return True

    def _extract_project_info(self):
        """
        Extracts project information from the provided document.

        Returns:
            dict: A dictionary containing selected project information or an empty dictionary in case of an error.
        """
        try:
            project_info = {
                "project_name": self.doc.get("project_name", ""),
                "project_id": self.doc.get("project_id", "Unknown_Project"),
                "escg_id": self.doc.get("customer_project_reference"),
                "library_prep_option": self.doc.get("details", {}).get(
                    "library_prep_option"
                ),
                "contact": self.doc.get("contact"),  # Is this an email or a name?
                "ref_genome": self.doc.get("reference_genome"),
                "organism": self.doc.get("details", {}).get("organism"),
                "sequencing_setup": self.doc.get("details", {}).get("sequencing_setup"),
            }

            return project_info
        except Exception as e:
            logging.error(f"Error occurred while extracting project information: {e}")
            return (
                {}
            )  # Return an empty dict or some default values to allow continuation

    # TODO: Check whether this would be better fit in the sample_file_handler
    def ensure_project_directory(self):
        """
        Ensures that the project directory exists.

        Returns:
            Path: The Path object of the directory if successful, or None if an error occurs.
        """
        try:
            project_dir = (
                Path(self.config["smartseq3_dir"])
                / "projects"
                / self.project_info["project_name"]
            )
            project_dir.mkdir(parents=True, exist_ok=True)
            return project_dir
        except Exception as e:
            logging.error(f"Failed to create project directory: {e}")
            return None

    async def launch(self):
        """Launch the SmartSeq3 Realm to handle its samples."""
        logging.info(
            f"Processing SmartSeq3 project {self.project_info['project_name']}"
        )
        self.status = "processing"

        # 1) Gather all samples, including aborted/unsequenced
        self.samples = self.extract_samples()
        if not self.samples:
            logging.warning("No samples found. Returning...")
            return

        # 2) Register them in YggdrasilDB
        self.add_samples_to_project_in_db()

        # 3) Filter only the truly processable samples (i.e. not aborted, not unsequenced)
        self.samples = self.select_samples_for_processing()

        if not self.samples:
            logging.warning("No valid (sequenced) samples to process. Returning...")
            return

        # 4) Pre-process samples
        pre_tasks = [sample.pre_process() for sample in self.samples]
        await asyncio.gather(*pre_tasks)

        # NOTE: Could control whether to proceed with processing based on config or parameters

        # Filter samples that passed pre-processing
        pre_processed_samples = [
            sample for sample in self.samples if sample.status == "pre_processed"
        ]

        if not pre_processed_samples:
            logging.warning("No samples passed pre-processing. Exiting...")
            return

        logging.info("\n")
        logging.info(
            f"Samples that passed pre-processing:"
            f"{[sample.id for sample in pre_processed_samples]}"
        )

        # 5) Process samples
        tasks = [sample.process() for sample in pre_processed_samples]
        logging.debug(f"Sample tasks created. Waiting for completion...: {tasks}")
        await asyncio.gather(*tasks)

        # Log samples that passed processing
        processed_samples = [
            sample for sample in pre_processed_samples if sample.status == "completed"
        ]
        logging.info("\n")
        logging.info(
            f"Samples that finished successfully: "
            f"{[sample.id for sample in processed_samples]}\n"
        )
        self.finalize_project()

    def extract_samples(self) -> List[SS3Sample]:
        """
        Gather **all** samples from the project document, including aborted or unsequenced.

        The sample's status is decided by the sample's constructor:
        - If 'aborted=True' is passed, the sample sets `_status="aborted"`.
        - Otherwise, it checks whether there is a flowcell ID and sets `_status="
            initialized" or "unsequenced".

        Returns:
            list: A list of SS3Sample instances.
        """
        samples = []

        # Iterate over all samples in the project doc
        for sample_id, sample_data in self.doc.get("samples", {}).items():
            # Check if the manual status in the project doc is "aborted"
            manual_status = (
                sample_data.get("details", {}).get("status_(manual)", "").lower()
            )
            is_aborted = manual_status == "aborted"

            # Instantiate the SS3Sample
            sample = SS3Sample(
                sample_id=sample_id,
                sample_data=sample_data,
                project_info=self.project_info,
                config=self.config,
                yggdrasil_db_manager=self.ydm,
                aborted=is_aborted,
            )
            samples.append(sample)

        return samples

    def select_samples_for_processing(self) -> List[SS3Sample]:
        """
        Return only the samples that should be processed right now:
        e.g. skip aborted or unsequenced.
        """
        processable = []
        for sample in self.samples:
            # If a sample is aborted or unsequenced, skip
            if sample.status in ("aborted", "unsequenced"):
                logging.info(
                    f"Skipping sample '{sample.id}' => status '{sample.status}'"
                )
                continue
            # Otherwise it's "initialized" => we can process it
            processable.append(sample)

        return processable

    def finalize_project(self):
        """
        Finalizes the project by generating reports and handling any post-processing (such as preparing deliveries).
        """
        self._generate_ngi_report()

    def _generate_ngi_report(self):
        """
        Generates the NGI report for the project.
        """
        # TODO: Find a way to use the name of the user who signs. For Ygg-mule it could be an argument, but what about Ygg-trunk? Slack maybe?
        user_name = "Anastasios Glaros"
        sample_list = [sample.id for sample in self.samples]
        project_path = str(self.project_dir)
        project_id = self.project_info.get("project_id", "Unknown_Project")

        report_success = generate_ngi_report(
            project_path, project_id, user_name, sample_list
        )
        if report_success:
            logging.info("NGI report was generated successfully.")
        else:
            logging.error("Failed to generate the NGI report.")

    def create_slurm_job(self, sample):
        """
        Placeholder for creating a Slurm job on the project level.
        Not used in the current implementation, but demanded by the template class (perhaps reconsider template).
        """
        pass

    # def submit_job(self, script):
    #     """
    #     Submits a job to Slurm. This uses the JobManager's functionality.
    #     """
    #     # Use JobManager to submit the job
    #     return super().submit_job(script)

    # def monitor_job(self, job_id):
    #     """
    #     Monitors the submitted Slurm job. This uses the JobManager's functionality.
    #     """
    #     # Use JobManager to monitor the job
    #     return super().monitor_job(job_id)

    def post_process(self, result):
        """
        Post-process method placeholder.

        Args:
            result: Result to post-process.
        """
        pass

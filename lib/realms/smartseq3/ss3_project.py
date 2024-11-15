import asyncio
from pathlib import Path

from lib.base.abstract_project import AbstractProject
from lib.core_utils.config_loader import ConfigLoader
from lib.core_utils.logging_utils import custom_logger
from lib.module_utils.ngi_report_generator import generate_ngi_report

# from datetime import datetime
# from lib.couchdb.manager import YggdrasilDBManager
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
        self.doc = doc
        self.ydm = yggdrasil_db_manager
        self.proceed = self._check_required_fields()

        # TODO: What if I return None if not self.proceed?
        if self.proceed:
            self.project_info = self._extract_project_info()
            self.project_dir = self.ensure_project_directory()
            self.project_info["project_dir"] = self.project_dir
            self.samples = []

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

    def _check_required_fields(self):
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

        self.samples = self.extract_samples()
        if not self.samples:
            logging.warning("No samples found for processing. Returning...")
            return

        # Pre-process samples
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

        # Process samples
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

    def extract_samples(self):
        """
        Extracts samples from the document and creates SS3Sample instances.

        Returns:
            list: A list of SS3Sample instances.
        """
        samples = []

        for sample_id, sample_data in self.doc.get("samples", {}).items():
            sample = SS3Sample(sample_id, sample_data, self.project_info, self.config)

            if sample.flowcell_id:
                samples.append(sample)
            else:
                logging.warning(f"Skipping {sample_id}. No flowcell IDs found.")

        return samples

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
        Not used in the current implementation, but demanded by the RealmTemplate (perhaps reconsider template).
        """
        # try:
        #     output_file = f"sim_out/10x/{sample['scilife_name']}_slurm_script.sh"
        #     # Use your method to generate the Slurm script here
        #     generate_slurm_script(sample, "sim_out/10x/slurm_template.sh", output_file)
        # except Exception as e:
        #     logging.warning(f"Error in creating Slurm job for sample {sample['scilife_name']}: {e}")
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

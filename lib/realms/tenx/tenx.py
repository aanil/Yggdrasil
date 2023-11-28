import logging
import asyncio

from lib.branches._10x.gex import GEXProject
from lib.branches._10x.atac import ATACSeqProject
from lib.branches._10x import vdj
from lib.branches._10x import multiome

from lib.utils.branch_template import RealmTemplate
from lib.utils.destiny_interface import DestinyInterface
from lib.utils.config_loader import ConfigLoader
from lib.utils.slurm_utils import generate_slurm_script
from lib.branches._10x.utils._10x_utils import collect_meta_per_sample
from lib.utils.couch_utils import has_required_fields


class TenX(DestinyInterface, RealmTemplate):
    # Class variables
    config = ConfigLoader().load_config_path("lib/branches/_10x/10x_config.json")

    def __init__(self, doc):
        self.doc = doc
        self.proceed = self._check_required_fields()

        # TODO: Where is best to have this?
        self.project_type = {
            "Chromium: 3' GEX": GEXProject,
            "Chromium: ATAC-seq": ATACSeqProject,
            # ... other strategies ...
        }

        if self.proceed:
            self.project_info = self._extract_project_info()
            self.project_instance = self._initialize_project()
        

    def _initialize_project(self):
        """
        Initializes a project based on the library prep option specified in the document.

        :return: An instance of the appropriate project class.
        """
        try:
            project_method = self.doc.get('details', {}).get('library_prep_option')
            project_class = self.project_type.get(project_method)

            if project_class:
                logging.info(f"Initializing project class for \"{project_method}\".")
                return project_class(self.project_info)
            else:
                logging.warning(f"No project class found for \"{project_method}\".")
                return None
        except Exception as e:
            logging.warning(f"Error while initializing project: {e}")
            return None

    async def process(self):
        if self.project_instance:
            try:
                await self.project_instance.process(self.doc)
            except Exception as e:
                logging.warning(f"Error in strategy execution: {e}")


    def _extract_project_info(self):
        """
        Extracts project information from the provided document.

        :return: A dictionary containing selected project information or an empty dictionary in case of an error.
        """
        try:
            project_info = {
                "project_name": self.doc.get('project_name', '').replace(".", "__"),
                "project_id": self.doc.get('project_id'),
                "escg_id": self.doc.get('customer_project_reference'),
                "library_prep_option": self.doc.get('details', {}).get('library_prep_option'),
                "contact": self.doc.get('contact'),  # Is this an email or a name?
                "ref_genome": self.doc.get('reference_genome'),
            }

            return project_info

        except Exception as e:
            logging.error(f"Error occurred while extracting project information: {e}")
            return {}  # Return an empty dict or some default values to allow continuation

    def _check_required_fields(self):
        required_fields = self.config.get("required_fields", [])
        missing_keys = [field for field in required_fields if not self._is_field(field, self.doc)]
        
        if missing_keys:
            logging.warning(f"Missing required project information: {missing_keys}. - {self.doc.get('project_id')}")
            return False
        return True

    def _is_field(self, field_path, data):
        """Check if a nested field exists in a dictionary."""
        keys = field_path.split('.')
        for key in keys:
            if isinstance(data, dict) and key in data:
                data = data[key]
            else:
                return False
        return True

    def pre_process(self, doc):
        pass
    # def pre_process(self, doc):
    #     try:
    #         # print(doc['details']['library_prep_option'])
    #         if 'library_prep_option' in doc['details']:
    #         # if doc['details']['library_prep_option']:
    #             prep_option = doc['details']['library_prep_option']
    #             tenx_config = ConfigLoader().load_config_path("lib/branches/_10x/10x_config.json")

    #             if has_required_fields(doc, tenx_config["required_fields"]):
    #                 self._process_prep(prep_option, doc)
    #             else:
    #                 logging.warning(f"Missing required fields for 10X processing.")
    #         else:
    #             logging.warning("No library_prep_option found.")
    #             return False
    #     except Exception as e:
    #         logging.warning(f"10X: Error while processing couchDB data: {e}")
    #         return False

    def create_slurm_job(self, sample):
        try:
            output_file = f"sim_out/10x/{sample['scilife_name']}_slurm_script.sh"
            # Use your method to generate the Slurm script here
            generate_slurm_script(sample, "sim_out/10x/slurm_template.sh", output_file)
        except Exception as e:
            logging.warning(f"Error in creating Slurm job for sample {sample['scilife_name']}: {e}")

    def submit_job(self, script):
        """
        Submits a job to Slurm. This uses the JobManager's functionality.
        """
        # Use JobManager to submit the job
        return super().submit_job(script)

    def monitor_job(self, job_id):
        """
        Monitors the submitted Slurm job. This uses the JobManager's functionality.
        """
        # Use JobManager to monitor the job
        return super().monitor_job(job_id)
    
    def post_process(self, result):
        """
        Concrete implementation of the post_process method.
        """
        pass

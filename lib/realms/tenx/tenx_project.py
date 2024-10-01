import re
import asyncio
import logging
from pathlib import Path

from lib.couchdb.manager import YggdrasilDBManager

from lib.core_utils.realm_template import RealmTemplate
from lib.core_utils.config_loader import ConfigLoader

from lib.realms.tenx.lab_sample import TenXLabSample
from lib.realms.tenx.run_sample import TenXRunSample

from lib.core_utils.logging_utils import custom_logger

logging = custom_logger(__name__.split('.')[-1])


class TenXProject(RealmTemplate):
    """
    Class representing a SmartSeq3 project.
    """

    config = ConfigLoader().load_config("10x_config.json")

    def __init__(self, doc, yggdrasil_db_manager):
        """
        Initialize a TenXProject instance.

        Args:
            doc (dict): Document containing project metadata.
        """
        self.doc = doc  # Document with project details
        self.ydm = yggdrasil_db_manager  # YggdrasilDBManager instance

        # TODO: Might need to check required fields for each different method, if they differ
        self.proceed = self._check_required_fields()  # Check if required fields are present

        if self.proceed:
            # Extract metadata from project document
            self.project_info = self._extract_project_info()

            if not self.determine_organism():
                # TODO: Send this message as a notification (maybe on Slack?)
                logging.error("Project organism could not be determined. Handle manually!")
                self.proceed = False
                return
            
            self.project_dir = self.ensure_project_directory()  # Ensure project directory is created
            self.samples = []  # List of TenXSample instances
            self.case_type = self.project_info.get("case_type")
            logging.info(f"Case type: {self.case_type}")
        
            self.status = "initialized"

    def _extract_project_info(self):
        """
        Extracts relevant project information from the document.
        
        Returns:
            dict: A dictionary containing extracted project info.
        """
        try:
            details = self.doc.get('details', {})
            project_info = {
                "project_name": self.doc.get('project_name', '').replace(".", "__"),
                "project_id": self.doc.get('project_id', 'Unknown_Project'),
                "customer_reference": self.doc.get('customer_project_reference', ''),
                "library_prep_method": details.get('library_construction_method', ''),
                "library_prep_option": details.get('library_prep_option', ''),
                "reference_genome": self.doc.get('reference_genome', ''),
                "organism": details.get('organism', ''),
                "contact": self.doc.get('contact', '')
            }

            # Determine case type based on library_prep_option
            if project_info["library_prep_option"]:
                project_info["case_type"] = "old_format"  # Old case, because library_prep_option is populated
            else:
                project_info["case_type"] = "new_format"  # New case, because library_prep_option is empty or missing
                # Add new UDFs for the new case
                project_info.update({
                    "hashing": details.get('library_prep_option_single_cell_hashing', 'None'),
                    "cite": details.get('library_prep_option_single_cell_cite', 'None'),
                    "vdj": details.get('library_prep_option_single_cell_vdj', 'None'),
                    "feature": details.get('library_prep_option_single_cell_feature', 'None')
                })

            return project_info
        except Exception as e:
            logging.error(f"Error occurred while extracting project information: {e}")
            return {}


    def determine_organism(self):
        """
        Determines the organism for the project by parsing the 'reference_genome' field first,
        then falling back to the 'organism' field. Updates 'project_info' with the organism.
        """
        # Try to extract organism from 'reference_genome' field
        reference_genome = self.project_info.get('reference_genome', '').strip()
        if reference_genome and reference_genome.lower() != 'other (-, -)':
            # Split at '(' and take the first part
            organism = reference_genome.split('(')[0].strip().lower()
            # Validate organism
            if self.is_supported_organism(organism):
                self.project_info['organism'] = organism
                return True
        # If 'reference_genome' is not usable, try 'organism' field
        organism = self.project_info.get('organism', '').strip().lower()
        if organism and self.is_supported_organism(organism):
            self.project_info['organism'] = organism
            return True
        # If neither field is usable, log an error
        logging.error(f"Organism '{organism}' not specified or unsupported for project '{self.project_info['project_name']}'")
        self.status = "failed"
        return False


    def is_supported_organism(self, organism):
        """
        Checks if the given organism is supported based on the 'gex' references in the configuration.
        """
        reference_mapping = self.config.get('reference_mapping', {})
        gex_organisms = reference_mapping.get('gex', {}).keys()
        return organism in gex_organisms


    def _check_required_fields(self):
        """
        Checks if the document contains all required fields.

        Returns:
            bool: True if all required fields are present, False otherwise.
        """
        required_fields = self.config.get("required_fields", [])

        missing_keys = [field for field in required_fields if not self._is_field(field, self.doc)]
        
        if missing_keys:
            logging.warning(f"Missing required project information: {missing_keys}.")
            return False

        return True
    

    def _is_field(self, field_path, data):
        """
        Checks if the document contains all required fields.

        Returns:
            bool: True if all required fields are present, False otherwise.
        """
        keys = field_path.split('.')
        for key in keys:
            if isinstance(data, dict) and key in data:
                data = data[key]
            else:
                return False
        return True


    def ensure_project_directory(self):
        """
        Ensures that the project directory exists. Creates it if necessary.

        Returns:
            Path: The Path object of the project directory.
        """
        try:
            project_base_dir = Path(self.config['10x_dir'])
            project_dir = project_base_dir / self.project_info['project_name']
            project_dir.mkdir(parents=True, exist_ok=True)
            return project_dir
        except Exception as e:
            logging.error(f"Failed to create project directory: {e}")
            return None


    # def extract_subsamples_old_case(self):
    #     """
    #     Extract subsamples for an old case based on known suffixes in the sample ID.
        
    #     Args:
    #         sample_data (dict): Dictionary of all samples from the project document.
        
    #     Returns:
    #         dict: A dictionary grouping original samples with their corresponding subsamples.
    #     """
    #     subsample_groups = {}
    #     # known_suffixes = self.config.get('old_suffixes', [])
    #     sample_data = self.doc.get('samples', {})

    #     for sample_id, sample_info in sample_data.items():
    #         # Check if the sample is aborted
    #         status_manual = sample_info.get('details', {}).get('status_(manual)', '').lower()
    #         if status_manual == 'aborted':
    #             logging.info(f"Sample {sample_id} is marked as 'Aborted' and will be skipped.")
    #             continue  # Skip this sample

    #         feature, original_sample_id = self.identify_feature_old(sample_info)
            
    #         if feature:
    #             logging.info(f"Found subsample {sample_id} with feature {feature.upper()}")
    #             # This is a subsample, find its original sample (e.g., X3_24_025 for X3_24_025_HTO)
    #             # TODO: This will not work in cases such as X3_24_025_HTO_rerun. Find a more robust way
    #             # original_sample_id = sample_info.get('customer_name', '').replace(f"_{feature.upper()}", '')
    #             if original_sample_id not in subsample_groups:
    #                 subsample_groups[original_sample_id] = []

    #             # Add subsample to its corresponding original sample group
    #             subsample_groups[original_sample_id].append(TenXSubsample(sample_id, feature, sample_info, self.project_info))
    #         else:
    #             logging.info(f"Found original sample {sample_id}")
    #             library_prep_option = self.project_info.get('library_prep_option')
    #             feature = self.get_default_feature(library_prep_option)
    #             # If it's an original sample (no known suffix), ensure it's in the group
    #             if sample_id not in subsample_groups:
    #                 subsample_groups[sample_id] = []  # No subsamples found yet

    #     # Create a list of TenXSample (or Original/CompositeSample) instances
    #     tenx_samples = []
    #     for original_sample_id, subsamples in subsample_groups.items():
    #         if subsamples:
    #             # Create a CompositeSample if there are subsamples
    #             tenx_samples.append(TenXCompositeSample(original_sample_id, subsamples, self.project_info, self.config, self.ydm))
    #         else:
    #             # Create an OriginalSample if there are no subsamples
    #             tenx_samples.append(TenXOriginalSample(original_sample_id, sample_data[original_sample_id], self.project_info, self.config, self.ydm))

    #     return tenx_samples
    

    def get_default_feature(self, library_prep_id):
        patterns = ["3' GEX", "5' GEX", "3GEX", "5GEX", "VDJ"]
        if any(pattern in library_prep_id for pattern in patterns):
            return 'gex'
        elif 'ATAC' in library_prep_id:
            return 'atac'
        else:
            return 'unknown'


    def identify_feature_old_case(self, sample_info):
        feature_map = self.config['feature_map']['old_format']
        customer_name = sample_info.get('customer_name', '')
        for assay_suffix, feature in feature_map.items():
            suffix_with_underscore = f"_{assay_suffix}"
            if suffix_with_underscore in customer_name:
                original_sample_id = customer_name.split(suffix_with_underscore)[0]
                return feature, original_sample_id
        return None, None


    def identify_feature_new_case(self, sample_id):
        feature_map = self.config['feature_map']['new_format']
        assay_digit = sample_id[-1]
        feature = feature_map.get(assay_digit)
        return feature


    # # TODO: TEST THIS VIGOOROUSLY! No examples exist for this case yet.
    # def extract_subsamples_new_case(self):
    #     subsample_groups = {}
    #     sample_data = self.doc.get('samples', {})

    #     for sample_id, sample_info in sample_data.items():
    #         # Check if the sample is aborted
    #         status_manual = sample_info.get('details', {}).get('status_(manual)', '').lower()
    #         if status_manual == 'aborted':
    #             logging.info(f"Sample {sample_id} is marked as 'Aborted' and will be skipped.")
    #             continue  # Skip this sample

    #         feature = self.identify_feature(sample_id, 'new_format')
    #         if feature:
    #             original_sample_id = sample_id[:-1]  # Remove the assay digit
    #             subsample = TenXSubsample(sample_id, feature, sample_info, self.project_info)
    #             if original_sample_id not in subsample_groups:
    #                 subsample_groups[original_sample_id] = []
    #             subsample_groups[original_sample_id].append(subsample)
    #         else:
    #             # logging.warning(f"No special assay identified for sample {sample_id}")
    #             logging.info(f"Found original sample {sample_id}")
    #             library_prep_method = self.project_info.get('library_prep_method')
    #             feature = self.get_default_feature(library_prep_method)

    #     # Create TenXCompositeSample instances
    #     tenx_samples = []
    #     for original_sample_id, subsamples in subsample_groups.items():
    #         if len(subsamples) > 1:
    #             tenx_samples.append(TenXCompositeSample(original_sample_id, subsamples, self.project_info, self.config, self.ydm))
    #         else:
    #             tenx_samples.append(TenXOriginalSample(original_sample_id, subsamples[0].sample_data, self.project_info, self.config, self.ydm))
    #     return tenx_samples

    def filter_aborted_samples(self, sample_data):
        return {
            sample_id: sample_info
            for sample_id, sample_info in sample_data.items()
            if sample_info.get('details', {}).get('status_(manual)', '').lower() != 'aborted'
        }


    def identify_feature_and_original_id_old(self, sample_id, sample_info):
        feature, original_sample_id = self.identify_feature_old_case(sample_info)
        if feature:
            return feature, original_sample_id
        else:
            # Handle original samples without features
            library_prep_option = self.project_info.get('library_prep_option')
            feature = self.get_default_feature(library_prep_option)
            original_sample_id = sample_id
            return feature, original_sample_id


    def identify_feature_and_original_id_new(self, sample_id):
        feature, original_sample_id = self.identify_feature_new_case(sample_id)
        if feature:
            return feature, original_sample_id
        else:
            library_prep_method = self.project_info.get('library_prep_method')
            feature = self.get_default_feature(library_prep_method)
            original_sample_id = sample_id
            return feature, original_sample_id


    def create_lab_samples(self, sample_data):
        lab_samples = {}
        for sample_id, sample_info in sample_data.items():
            if self.case_type == 'old_format':
                feature, original_sample_id = self.identify_feature_and_original_id_old(sample_id, sample_info)
            else:
                feature, original_sample_id = self.identify_feature_and_original_id_new(sample_id)

            lab_sample = TenXLabSample(sample_id, feature, sample_info, self.project_info)
            lab_samples[sample_id] = (lab_sample, original_sample_id)
        return lab_samples


    def group_lab_samples(self, lab_samples):
        groups = {}
        for lab_sample, original_sample_id in lab_samples.values():
            groups.setdefault(original_sample_id, []).append(lab_sample)
        return groups


    def create_run_samples(self, grouped_lab_samples):
        run_samples = []
        for original_sample_id, lab_samples in grouped_lab_samples.items():
            run_sample = TenXRunSample(original_sample_id, lab_samples, self.project_info, self.config, self.ydm)
            run_samples.append(run_sample)
        return run_samples


    def extract_samples(self):
        sample_data = self.doc.get('samples', {})
        # Step 1: Filter aborted samples
        sample_data = self.filter_aborted_samples(sample_data)
        # Step 2: Create lab samples
        lab_samples = self.create_lab_samples(sample_data)
        # Step 3: Group lab samples by original sample ID
        grouped_lab_samples = self.group_lab_samples(lab_samples)
        # Step 4: Create run samples
        run_samples = self.create_run_samples(grouped_lab_samples)
        return run_samples


    def pre_process(self):
        """
        Perform any pre-processing steps required before processing the project.
        """
        pass

    async def process(self):
        """
        Process the TenX project by handling its samples.
        """
        logging.info(f"Processing TenX project {self.project_info['project_name']}")
        self.status = "processing"


        self.samples = self.extract_samples()

        logging.info(f"Samples to be processed: {[sample.run_sample_id for sample in self.samples]}")
        logging.info(f"Sample features: {[sample.features for sample in self.samples]}")

        if not self.samples:
            logging.warning("No samples found for processing. Returning...")
            return

        # Process each sample asynchronously
        tasks = [sample.process() for sample in self.samples]
        await asyncio.gather(*tasks)
        
        logging.info(f"All samples processed for project {self.project_info['project_name']}")
        self.finalize_project()

    def create_slurm_job(self, data):
        pass

    def post_process(self, result):
        pass

    def finalize_project(self):
        """
        Finalize the project by handling post-processing steps (e.g., report generation).
        """
        logging.info(f"Finalizing project {self.project_info['project_name']}")
        # Placeholder for any project-level finalization steps, like report generation, cleanup, etc.
        self.status = "completed"
        logging.info(f"Project {self.project_info['project_name']} has been successfully finalized.")



    

        
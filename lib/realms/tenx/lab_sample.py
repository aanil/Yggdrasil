import glob
import logging

from pathlib import Path

from lib.utils.config_loader import ConfigLoader

from lib.utils.logging_utils import custom_logger

logging = custom_logger(__name__.split('.')[-1])

class TenXLabSample:
    config = ConfigLoader().load_config("10x_config.json")

    def __init__(self, lab_sample_id, feature, sample_data, project_info):
        """
        Initialize a LabSample instance.

        Args:
            lab_sample_id (str): ID of the lab sample (e.g. X3_24_025_GE).
        """
        self.lab_sample_id = lab_sample_id
        self.project_info = project_info
        self.feature = feature
        self.sample_data = sample_data

        self.organism = self.project_info['organism']
        self.lims_id = sample_data.get('sample_id')
        self.flowcell_ids = self._get_all_flowcells()
        self.fastq_dirs = self.locate_fastq_dirs()
        self.reference_genome = self.get_reference_genome()

        # logging.debug(f"Reference genome for sample {self.lab_sample_id}: {self.reference_genome}")


    def _get_all_flowcells(self):
        """
        Collect all flowcell IDs associated with the sample.
        
        Returns:
            list: A list of flowcell IDs for the sample.
        """
        try:
            flowcell_ids = []
            if 'library_prep' in self.sample_data:
                for prep_info in self.sample_data['library_prep'].values():
                    flowcell_ids.extend(prep_info.get('sequenced_fc', []))
            
            if not flowcell_ids:
                logging.warning(f"No valid flowcells found for sample {self.lab_sample_id}.")
            return flowcell_ids
        except Exception as e:
            logging.error(f"Error while fetching flowcell IDs for sample '{self.lab_sample_id}': {e}", exc_info=True)
            return None


    def locate_fastq_dirs(self):
        """
        Locate the parent directories of the FASTQ files for each flowcell.
        
        Returns:
            dict: A dictionary mapping flowcell IDs to their respective parent directories.
        """
        fastq_dirs = {}
        for flowcell_id in self.flowcell_ids:
            pattern = Path(self.config['seq_root_dir'], self.project_info.get('project_id', ''), self.lab_sample_id, '*', flowcell_id)
            fastq_dir = glob.glob(str(pattern))

            if fastq_dir:
                fastq_dirs[flowcell_id] = fastq_dir
            else:
                logging.warning(f"No FASTQ directory found for flowcell {flowcell_id} in sample {self.lab_sample_id}")

        if not fastq_dirs:
            logging.warning(f"No FASTQ directories found for sample {self.lab_sample_id}.")
            return None
        
        return fastq_dirs
    

    def get_reference_genome(self):
        """
        Get the reference genome path for a given feature based on the organism.
        """
        reference_mapping = self.config.get('reference_mapping', {})
        feature_to_ref_key = self.config.get('feature_to_ref_key', {})

        ref_key = feature_to_ref_key.get(self.feature)

        if not ref_key:
            logging.error(f"Feature '{self.feature}' is not recognized for reference genome mapping.")
            return None
        
        refs_map = reference_mapping.get(ref_key)
        if not refs_map:
            logging.error(f"No reference genomes found for reference key '{ref_key}'")
            return None

        ref_genome = refs_map.get(self.organism)
        if not ref_genome:
            logging.error(f"No reference genome found for feature '{self.feature}' (mapped to '{ref_key}') and organism '{self.organism}'")
            return None

        return ref_genome
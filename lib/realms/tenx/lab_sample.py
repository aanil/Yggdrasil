import glob
import logging

from pathlib import Path

from lib.utils.config_loader import ConfigLoader

class TenXLabSample:
    config = ConfigLoader().load_config("10x_config.json")

    def __init__(self, sample_id, feature, sample_data, project_info):
        """
        Initialize a LabSample instance.

        Args:
            sample_id (str): ID of the lab sample (e.g. X3_24_025_GE).
        """
        self.sample_id = sample_id
        self.project_info = project_info
        self.feature = feature
        self.sample_data = sample_data
        self.flowcell_ids = self._get_all_flowcells()
        self.fastq_dirs = self.locate_fastq_dirs()


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
                logging.warning(f"No valid flowcells found for sample {self.sample_id}.")
            return flowcell_ids
        except Exception as e:
            logging.error(f"Error while fetching flowcell IDs for sample '{self.sample_id}': {e}", exc_info=True)
            return None


    def locate_fastq_dirs(self):
        """
        Locate the parent directories of the FASTQ files for each flowcell.
        
        Returns:
            dict: A dictionary mapping flowcell IDs to their respective parent directories.
        """
        fastq_dirs = {}
        for flowcell_id in self.flowcell_ids:
            pattern = Path(self.config['seq_root_dir'], self.project_info.get('project_id', ''), self.sample_id, '*', flowcell_id)
            fastq_dir = glob.glob(str(pattern))

            if fastq_dir:
                fastq_dirs[flowcell_id] = fastq_dir
            else:
                logging.warning(f"No FASTQ directory found for flowcell {flowcell_id} in sample {self.sample_id}")

        if not fastq_dirs:
            logging.warning(f"No FASTQ directories found for sample {self.sample_id}.")
            return None
        
        return fastq_dirs
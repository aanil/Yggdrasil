import csv
import json
import logging
from pathlib import Path
from lib.core_utils.common import YggdrasilUtilities as Ygg


class TenXUtils():

    # TODO: Should this be here as a static method?
    # @staticmethod
    # def generate_library_csv(library_csv_path):
    #     with open(library_csv_path, 'w') as csvfile:
    #         writer = csv.writer(csvfile)
    #         writer.writerow(['fastqs', 'sample', 'library_type'])
    #         for subsample in self.subsamples:
    #             fastq_paths = subsample.fastq_dirs  # Assuming this is a list of paths
    #             fastqs = ','.join(map(str, fastq_paths))
    #             writer.writerow([fastqs, subsample.sample_id, subsample.assay])


    @staticmethod
    def load_decision_table(file_name):
        """
        Load the decision table JSON file.

        Args:
            file_name (str): The name of the decision table JSON file.

        Returns:
            list: The loaded decision table as a list of dictionaries.
        """
        config_file = Ygg.get_path(file_name)
        if config_file is None:
            logging.error(f"Decision table file '{file_name}' not found.")
            return []

        try:
            with open(config_file, "r") as f:
                decision_table = json.load(f)
                if not isinstance(decision_table, list):
                    logging.error(f"Decision table '{file_name}' is not a list.")
                    return []
                return decision_table
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing decision table '{file_name}': {e}")
            return []
        except Exception as e:
            logging.error(f"Unexpected error loading decision table '{file_name}': {e}")
            return []
        

    @staticmethod
    def get_pipeline_info(library_prep_method, features):
        for entry in TenXUtils.load_decision_table("10x_decision_table.json"):
            if (
                entry['library_prep_method'] == library_prep_method and
                set(entry['features']) == set(features)
            ):
                return entry
        return None
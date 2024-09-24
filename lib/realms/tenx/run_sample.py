import csv
import logging

from lib.realms.tenx.utils.sample_file_handler import SampleFileHandler
from lib.realms.tenx.utils.tenx_utils import TenXUtils



class TenXRunSample:
    def __init__(self, sample_id, lab_samples, project_info, config, yggdrasil_db_manager, **kwargs):
        self.sample_id = sample_id
        self.lab_samples = lab_samples
        self.project_info = project_info
        self.config = config
        self.ydm = yggdrasil_db_manager

        # self.decision_table = TenXUtils.load_decision_table("10x_decision_table.json")
        self.feature_to_library_type = self.config.get('feature_to_library_type', {})
        self.status = "initialized"
        self.file_handler = SampleFileHandler(self)


    async def process(self):
        """
        Process the sample.
        """
        logging.info(f"Processing sample {self.sample_id}")

        # Step 1: Verify that all subsamples have FASTQ files
        # TODO: Also check any other requirements
        missing_fq_labsamples = [lab_sample.sample_id for lab_sample in self.lab_samples if not lab_sample.fastq_dirs]
        if missing_fq_labsamples:
            logging.error(f"Run-sample {self.sample_id} is missing FASTQ files for lab-samples: {missing_fq_labsamples}. Skipping...")
            self.status = "failed"
            return
        
        features = [lab_sample.feature for lab_sample in self.lab_samples]
        features = list(set(features))

        library_prep_method = self.project_info.get('library_prep_method')

        # Step 4: Determine the pipeline and additional files required
        pipeline_info = TenXUtils.get_pipeline_info(library_prep_method, features)
        if not pipeline_info:
            logging.error(f"No pipeline information found for sample {self.sample_id}")
            self.status = "failed"
            return

        pipeline = pipeline_info.get('pipeline')
        additional_files = pipeline_info.get('additional_files', [])

        logging.info(f"Pipeline: {pipeline}")
        logging.info(f"Additional files: {additional_files}")

        logging.info(f"Generating additional files for composite sample {self.sample_id}")

        if 'libraries' in additional_files:
            self.generate_libraries_csv()
        if 'hash_ref' in additional_files:
            self.generate_feature_reference_csv()
        if 'multi' in additional_files:
            self.generate_multi_sample_csv()
            
        self.status = "processing"


    def generate_libraries_csv(self):
        logging.info(f"Generating library CSV for composite sample {self.sample_id}")
        library_csv_path = self.file_handler.base_dir / f'{self.sample_id}_libraries.csv'

        with open(library_csv_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=['fastqs', 'sample', 'library_type'])
            writer.writeheader()
            for lab_sample in self.lab_samples:
                feature_type = self.feature_to_library_type.get(lab_sample.feature)
                if not feature_type:
                    logging.error(f"Feature type not found for feature '{lab_sample.feature}' in sample '{lab_sample.sample_id}'")
                    continue
                # Write one row per FASTQ directory
                for paths in lab_sample.fastq_dirs.values():
                    for path in paths:
                        writer.writerow({
                            'fastqs': str(path),
                            'sample': lab_sample.sample_id,
                            'library_type': feature_type
                        })

    def generate_feature_reference_csv(self):
        logging.info(f"Generating feature reference CSV for composite sample {self.sample_id}")
        pass

    def generate_multi_sample_csv(self):
        logging.info(f"Generating multi-sample CSV for composite sample {self.sample_id}")
        pass
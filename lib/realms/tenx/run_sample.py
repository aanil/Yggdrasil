import csv
import logging

from lib.realms.tenx.utils.sample_file_handler import SampleFileHandler
from lib.realms.tenx.utils.tenx_utils import TenXUtils

from lib.utils.slurm_utils import generate_slurm_script

class TenXRunSample:
    def __init__(self, sample_id, lab_samples, project_info, config, yggdrasil_db_manager, **kwargs):
        self.run_sample_id = sample_id
        self.lab_samples = lab_samples
        self.project_info = project_info
        self.config = config
        self.ydm = yggdrasil_db_manager

        # self.decision_table = TenXUtils.load_decision_table("10x_decision_table.json")
        self.feature_to_library_type = self.config.get('feature_to_library_type', {})
        self.status = "initialized"
        self.file_handler = SampleFileHandler(self)

        self.features = self._collect_features()
        self.pipeline_info = self._get_pipeline_info()
        self.reference_genomes = self.collect_reference_genomes()

    def collect_reference_genomes(self):
        """
        Collect reference genomes from lab samples and ensure consistency.
        """
        ref_genomes = {}
        feature_to_ref_key = self.config.get('feature_to_ref_key', {})

        for lab_sample in self.lab_samples:
            if lab_sample.reference_genome:

                ref_key = feature_to_ref_key.get(lab_sample.feature)
                if not ref_key:
                    logging.error(f"Feature '{lab_sample.feature}' is not recognized for reference genome mapping.")
                    continue

                # TODO: test this logic - if existing ref same as another ref in lab sample, keep one e.g. take the set. Why fail this?
                # Ensure no conflicting reference genomes for the same ref_key
                existing_ref = ref_genomes.get(ref_key)
                if existing_ref and existing_ref != lab_sample.reference_genome:
                    logging.debug(f"Existing reference genome: {existing_ref} == {lab_sample.reference_genome}")
                    logging.error(f"Conflicting reference genomes found for reference key '{ref_key}' in sample '{self.run_sample_id}'")
                    self.status = "failed"
                    return None
                else:
                    ref_genomes[ref_key] = lab_sample.reference_genome
            else:
                logging.error(f"Lab sample {lab_sample.lab_sample_id} is missing a reference genome.")
                self.status = "failed"
                return None
        return ref_genomes


    def _get_pipeline_info(self):
        """
        Get the pipeline information for the sample.
        """
        library_prep_method = self.project_info.get('library_prep_method')
        return TenXUtils.get_pipeline_info(library_prep_method, self.features)


    def _collect_features(self):
        """
        Collect features from lab samples.
        """
        features = [lab_sample.feature for lab_sample in self.lab_samples] 
        return list(set(features))


    async def process(self):
        """
        Process the sample.
        """
        logging.info(f"Processing sample {self.run_sample_id}")

        # Step 1: Verify that all subsamples have FASTQ files
        # TODO: Also check any other requirements
        missing_fq_labsamples = [lab_sample.lab_sample_id for lab_sample in self.lab_samples if not lab_sample.fastq_dirs]
        if missing_fq_labsamples:
            logging.error(f"Run-sample {self.run_sample_id} is missing FASTQ files for lab-samples: {missing_fq_labsamples}. Skipping...")
            self.status = "failed"
            return

        # Step 4: Determine the pipeline and additional files required
        if not self.pipeline_info:
            logging.error(f"No pipeline information found for sample {self.run_sample_id}")
            self.status = "failed"
            return

        pipeline = self.pipeline_info.get('pipeline')
        pipeline_exec = self.pipeline_info.get('pipeline_exec')

        logging.info(f"Pipeline: {pipeline}")
        logging.info(f"Pipeline executable: {pipeline_exec}")

        logging.info(f"Generating required files for sample {self.run_sample_id}")
        if self.pipeline_info.get('libraries_csv'):
            self.generate_libraries_csv()
        if self.pipeline_info.get('feature_ref'):
            self.generate_feature_reference_csv()
        if self.pipeline_info.get('multi_csv'):
            self.generate_multi_sample_csv()

        cellranger_command = self.assemble_cellranger_command()

        slurm_metadata = {
            'sample_id': self.run_sample_id,
            'project_name': self.project_info.get('project_name'),
            'output_dir': str(self.file_handler.sample_dir),
            'cellranger_command': cellranger_command
        }

        logging.debug(f"Slurm metadata: {slurm_metadata}")
        
        slurm_template_path = self.config.get('slurm_template')
        if not generate_slurm_script(slurm_metadata, slurm_template_path, self.file_handler.slurm_script_path):
            logging.error(f"Failed to generate SLURM script for sample {self.run_sample_id}")
            return None

            
        self.status = "processing"



    def assemble_cellranger_command(self):
        command_parts = [
            f"{self.pipeline_info['pipeline_exec']} {self.pipeline_info['pipeline']}",
        ]
        
        required_args = self.pipeline_info.get('required_arguments', [])
        additional_args = self.pipeline_info.get('fixed_arguments', [])
        
        # Mapping of argument names to their values
        arg_values = {
            '--id': self.run_sample_id,
            # '--transcriptome': self.config.get('gene_expression_reference'),
            '--fastqs': ','.join([','.join(paths) for paths in self.lab_samples[0].fastq_dirs.values()]),
            '--sample': self.lab_samples[0].lab_sample_id,
            '--libraries': str(self.file_handler.base_dir / f'{self.run_sample_id}_libraries.csv'),
            '--feature-ref': str(self.file_handler.base_dir / f'{self.run_sample_id}_feature_reference.csv'),
            '--csv': str(self.file_handler.base_dir / f'{self.run_sample_id}_multi.csv')
        }
        
        if self.pipeline_info.get('pipeline') == 'count':
            if 'gex' in self.reference_genomes:
                arg_values['--transcriptome'] = self.reference_genomes['gex']
        elif self.pipeline_info.get('pipeline') == 'vdj':
            if 'vdj' in self.reference_genomes:
                arg_values['--reference'] = self.reference_genomes['vdj']
        elif self.pipeline_info.get('pipeline') == 'atac':
            if 'atac' in self.reference_genomes:
                arg_values['--reference'] = self.reference_genomes['atac']
        elif self.pipeline_info.get('pipeline') == 'multi':
            # references are specified in the multi-sample CSV file
            pass

        for arg in required_args:
            value = arg_values.get(arg)
            if value:
                command_parts.append(f"{arg}={value}")
        
        # Include additional arguments
        command_parts.extend(additional_args)
        
        # Join all parts into a single command string
        command = ' \\\n    '.join(command_parts)
        return command


    def generate_libraries_csv(self):
        logging.info(f"Generating library CSV for sample {self.run_sample_id}")
        library_csv_path = self.file_handler.base_dir / f'{self.run_sample_id}_libraries.csv'

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
                            'sample': lab_sample.lab_sample_id,
                            'library_type': feature_type
                        })

    def generate_feature_reference_csv(self):
        logging.info(f"Generating feature reference CSV for composite sample {self.run_sample_id}")
        pass

    def generate_multi_sample_csv(self):
        logging.info(f"Generating multi-sample CSV for composite sample {self.run_sample_id}")
        pass
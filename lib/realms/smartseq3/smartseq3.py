import logging
import asyncio

from pathlib import Path
from datetime import datetime

from lib.utils.sjob_manager import SlurmJobManager
from tests.utils.mock_sjob_manager import MockSlurmJobManager

from lib.utils.branch_template import RealmTemplate
from lib.utils.destiny_interface import DestinyInterface
from lib.utils.config_loader import ConfigLoader
from lib.utils.slurm_utils import generate_slurm_script
from lib.branches.smartseq3.utils.yaml_utils import write_yaml


DEBUG = True

class SmartSeq3(DestinyInterface, RealmTemplate):
    # Class variables
    config = ConfigLoader().load_config_path("lib/branches/smartseq3/ss3_config.json")

    def __init__(self, doc):
        self.doc = doc
        self.proceed = self._check_required_fields()

        # TODO: What if I return None if not self.proceed?
        if self.proceed:
            self.project_info = self._extract_project_info()

            self.project_dir = self.ensure_project_directory()
            self.project_info['project_dir'] = self.project_dir

            self.samples = []


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
                "sequencing_setup": self.doc.get('details', {}).get('sequencing_setup'),
            }

            return project_info

        except Exception as e:
            logging.error(f"Error occurred while extracting project information: {e}")
            return {}  # Return an empty dict or some default values to allow continuation

    def _check_required_fields(self):
        required_fields = self.config.get("required_fields", [])
        missing_keys = [field for field in required_fields if not self._is_field(field, self.doc)]
        
        if missing_keys:
            logging.warning(f"Missing required project information: {missing_keys}.")
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

    def ensure_project_directory(self):
        """
        Ensures that the project directory exists.
        Returns the Path object of the directory if successful, or None if an error occurs.
        """
        try:
            project_dir = Path(self.config['smartseq3_dir']) / 'projects' / self.project_info['project_name']
            project_dir.mkdir(parents=True, exist_ok=True)
            return project_dir
        except Exception as e:
            logging.error(f"Failed to create project directory: {e}")
            return None


    async def process(self):
        self.status = "processing"
        print("Processing SmartSeq3 project")
        self.samples = self.extract_samples()
        tasks = [sample.process() for sample in self.samples]
        print(f"Sample tasks created. Waiting for completion...: {tasks}")
        await asyncio.gather(*tasks)
        self.finalize_project(self.samples)

    def extract_samples(self):
        samples = []

        for sample_id, sample_data in self.doc.get('samples', {}).items():
            sample = SS3Sample(sample_id, sample_data, self.project_info, self.config)
            samples.append(sample)

        return samples

    def finalize_project(self, samples):
        # Logic to gather results and prepare for delivery
        pass
        


    def pre_process(self, doc):
        pass

    def create_slurm_job(self, sample):
        # try:
        #     output_file = f"sim_out/10x/{sample['scilife_name']}_slurm_script.sh"
        #     # Use your method to generate the Slurm script here
        #     generate_slurm_script(sample, "sim_out/10x/slurm_template.sh", output_file)
        # except Exception as e:
        #     logging.warning(f"Error in creating Slurm job for sample {sample['scilife_name']}: {e}")
        pass

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



class SS3Sample():
    def __init__(self, sample_id, sample_data, project_info, config):
        # TODO: self.id must be demanded by a template class
        self.id = sample_id
        self.sample_data = sample_data
        self.project_info = project_info
        self.config = config
        # self.job_id = None
        self.status = "pending"  # other statuses: "processing", "completed", "failed"

        if DEBUG:
            self.sjob_manager = MockSlurmJobManager()
        else:
            self.sjob_manager = SlurmJobManager()

    async def process(self):
        # Collect metadata for this sample
        print(f"Processing sample {self.id}")
        yaml_metadata = self._collect_yaml_metadata()
        if not yaml_metadata:
            logging.warning(f"Metadata missing for sample {self.id}")
            return None

        print("Metadata collected. Creating YAML file")

        self.create_yaml_file(yaml_metadata)

        print("YAML file created.")

        print("Creating Slurm script")
        slurm_metadata = self._collect_slurm_metadata()
        if not slurm_metadata:
            logging.warning(f"Slurm metadata missing for sample {self.id}")
            return None

        # Create Slurm script and submit job
        output_file = f"{self.project_info.get('project_dir')}/{self.id}_slurm_script.sh"
        slurm_template_path = self.config['slurm_template']
        slurm_script_path = generate_slurm_script(slurm_metadata, slurm_template_path, output_file)
        print("Slurm script created. Submitting job")
        self.job_id = await self.sjob_manager.submit_job(slurm_script_path)
        print(f"Job submitted with ID: {self.job_id}")

        # # Monitor the job
        # if self.job_id:
        #     await self.sjob_manager.monitor_job(self.job_id)

        # Monitor job asynchronously
        # asyncio.create_task(self.sjob_manager.monitor_job(self.job_id, self.check_status))
        asyncio.create_task(self.sjob_manager.monitor_job(self.job_id, self))

        print(f"Job {self.job_id} submitted for monitoring.")
        # Perform any necessary post-processing
        self.post_process()

    # TODO: Assess if this should be part of the SlurmJobManager class and move it there
    # def check_status(self, job_id, status):
    #     print(f"Job {job_id} status: {status}")
    #     if status == "COMPLETED":
    #         print(f"Sample {self.id} processing completed.")
    #         self.post_process()
    #         self.status = "completed"
    #     elif status in ["FAILED", "CANCELLED"]:
    #         self.status = "failed"
    #         print(f"Sample {self.id} processing failed.")


    def _collect_yaml_metadata(self):
        barcode = self.sample_data['library_prep']['A'].get('barcode', '').split('-')[-1]
        if not barcode:
            logging.warning(f"Barcode missing for sample {self.id}")
            return None
        
        bc_path = f"{self.config['smartseq3_dir']}/barcodes/{barcode}.txt"

        # TODO: If barcode does not exist, make barcode using mkbarcode
        if not Path(bc_path).exists():
            logging.warning(f"Barcode {barcode} not found at {bc_path}.")
            return None
        
        seq_root = self.config["seq_root_dir"]

        # NOTE: zUMIs does not support multiple flowcells per sample
        # SmartSeq3 sample libraries should not be sequenced across multiple flowcells
        # SmartSeq3 libraries should not be re-sequenced in the same project
        # Select the latest flowcell for analysis
        latest_fc = self._get_latest_flowcell(self.sample_data.get('library_prep', {}))
        if latest_fc:
            fastq_path = f"{seq_root}/{latest_fc}/Demultiplexing/{self.project_info['project_name']}/Sample_{self.id}"
            fastqs = self._list_fastq_files(fastq_path)
        else:
            logging.warning(f"No fastq files found for sample {self.id}")
            return None

        if not all(fastqs.values()):
            logging.warning(f"Not all fastq files found at {fastq_path}")
            return None
        
        seq_setup = self.project_info.get('sequencing_setup', '')
        if seq_setup:
            read_setup = self._transform_seq_setup(seq_setup)

        ref_gen = self.project_info.get('ref_genome', '')
        # NOTE: Might break if the reference genome format is odd.
        # TODO: Might need to make more robust or even map the ref genomes to their paths
        idx_path, gtf_path = self._get_ref_paths(ref_gen, self.config)

        if idx_path and gtf_path:
            ref_paths = {
                'gen_path': idx_path,
                'gtf_path': gtf_path
            }
        else:
            return None  # or handle the missing reference paths appropriately

        project_dir = self.project_info.get('project_dir')

        try:
            metadata = {
                # 'plate': self.id, # Temporarily not used, but might be used when we name everything after ngi
                'plate': self.sample_data.get('customer_name', ''),
                'bc_file': bc_path,
                'fastqs': {k: str(v) for k, v in fastqs.items() if v},
                'read_setup': read_setup,
                'ref': ref_paths,
                'outdir': str(project_dir),
                'out_yaml': project_dir / f"{self.id}.yaml"
            }
        except Exception as e:
            logging.error(f"Error constructing metadata for sample {self.id}: {e}")
            return None    

        return metadata
    
    def _get_latest_flowcell(self, library_prep):
        """
        Selects the latest flowcell for the given library prep information.

        Args:
            library_prep: The library preparation information from the sample data.
            sample_run_metrics: Sample run metrics containing sequencing_start_date.

        Returns:
            The latest flowcell ID.
        """
        latest_fc = None
        latest_date = None
        for prep in library_prep.values():
            for fc in prep.get('sequenced_fc', []):
                fc_date = self._parse_fc_date(fc)
                if fc_date and (not latest_date or fc_date > latest_date):
                    latest_date = fc_date
                    latest_fc = fc
        return latest_fc
    
    def _parse_fc_date(self, flowcell_id):
        """
        Parses the date from a flowcell ID, falls back to sequencing_start_date if needed.

        Args:
            flowcell_id: The flowcell ID to parse.
            sample_run_metrics: Sample run metrics containing sequencing_start_date.

        Returns:
            A date object representing the date of the flowcell.
        """
        date_formats = ['%Y%m%d', '%y%m%d']  # Potential date formats
        date_str = flowcell_id.split('_')[0]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                logging.warning(f"Could not parse date for flowcell {flowcell_id}.")
                return None

    def _list_fastq_files(self, fastq_path):
        """
        List and categorize fastq files in the given directory using pathlib.

        Args:
            fastq_path: The directory path where fastq files are located.

        Returns:
            A dictionary with keys 'R1', 'R2', 'I1', 'I2' and their respective file paths.
        """
        fastq_dir = Path(fastq_path)
        fastqs = {'R1': None, 'R2': None, 'I1': None, 'I2': None}

        if not fastq_dir.exists():
            logging.error(f"Fastq directory not found: {fastq_path}")
            return fastqs

        for file in fastq_dir.iterdir():
            if ''.join(file.suffixes) in ['.fastq.gz', '.fq.gz']:
                if '_R1_' in file.name:
                    fastqs['R1'] = file
                elif '_R2_' in file.name:
                    fastqs['R2'] = file
                elif '_I1_' in file.name:
                    fastqs['I1'] = file
                elif '_I2_' in file.name:
                    fastqs['I2'] = file

        return fastqs
    
    def _collect_slurm_metadata(self):
        project_dir = Path(self.config['smartseq3_dir']) / 'projects' / self.project_info['project_name']
        project_dir.mkdir(exist_ok=True)

        try:
            metadata = {
                'project_name': self.project_info['project_name'],
                # 'sample_id': self.id, # Temporarily not used, but might be used when we name everything after ngi
                'plate_id': self.sample_data.get('customer_name', ''),
                'yaml_settings_path': project_dir / f"{self.id}.yaml",
                'zumis_path': self.config['zumis_path'],
            }
        except Exception as e:
            logging.error(f"Error constructing metadata for sample {self.id}: {e}")
            return None    

        return metadata

    def _transform_seq_setup(self, seq_setup_str):
        """
        Transforms a sequencing setup string into a detailed format for each read type.

        Args:
            seq_setup_str (str): Sequencing setup string in the format "R1-I1-I2-R2".

        Returns:
            dict: A dictionary with formatted strings for each read type.
        """
        r1, i1, i2, r2 = seq_setup_str.split('-')

        return {
            'R1': (f"cDNA(23-{r1})", "UMI(12-19)"),
            'R2': f"cDNA(1-{r2})",
            'I1': f"BC(1-{i1})",
            'I2': f"BC(1-{i2})"
        }

    def _get_ref_paths(self, ref_gen, config):
        """
        Maps a reference genome to its STAR index and GTF file paths.

        Args:
            ref_gen (str): Reference genome string, e.g., "Zebrafish (Danio rerio, GRCz10)".
            config (dict): Configuration object containing the mapping.

        Returns:
            tuple: A tuple containing the STAR index path and GTF file path, or None if not found.
        """
        try:
            # Extract species name before the first comma
            species_key = ref_gen.split(',')[0].split('(')[1].strip().lower()
            idx_path = config['gen_refs'][species_key]['idx_path']
            gtf_path = config['gen_refs'][species_key]['gtf_path']
            return idx_path, gtf_path
        except KeyError as e:
            logging.warning(f"Reference for {e} species not found in config. Handle {self.id} manually.")
            return None, None


    def create_yaml_file(self, metadata):
        write_yaml(self.config, metadata)


    def post_process(self):
        print("Post-processing")
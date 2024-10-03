import csv
import glob
import logging
import subprocess
from pathlib import Path

from lib.core_utils.config_loader import ConfigLoader
from lib.module_utils.slurm_utils import generate_slurm_script
from lib.realms.tenx.utils.sample_file_handler import SampleFileHandler
from lib.realms.tenx.utils.tenx_utils import TenXUtils


class TenXSampleBase:
    def __init__(self, sample_id, project_info, config, yggdrasil_db_manager, **kwargs):
        self.sample_id = sample_id
        self.project_info = project_info
        self.config = config
        self.ydm = yggdrasil_db_manager

        self.feature_to_library_type = self.config.get("feature_to_library_type", {})
        self.status = "initialized"
        self.file_handler = SampleFileHandler(self)


class TenXCompositeSample(TenXSampleBase):
    def __init__(
        self, sample_id, subsamples, project_info, config, yggdrasil_db_manager
    ):
        """
        Represents a composite sample, consisting of multiple subsamples.

        Args:
            sample_id (str): ID of the composite sample.
            subsamples (list): List of TenXSubsample instances.
            project_info (dict): Metadata related to the parent project.
            config (dict): Configuration settings for the pipeline.
            yggdrasil_db_manager (YggdrasilDBManager): CouchDB manager instance for status tracking.
        """
        # Call the base class __init__
        super().__init__(sample_id, project_info, config, yggdrasil_db_manager)

        self.subsamples = subsamples
        self.decision_table = TenXUtils.load_decision_table("10x_decision_table.json")

    async def process(self):
        """
        Process the composite sample by handling its subsamples.
        """
        logging.info(f"Processing composite sample {self.sample_id}")

        # Step 1: Verify that all subsamples have FASTQ files
        # TODO: Also check any other requirements
        missing_fastq_subsamples = [
            subsample.sample_id
            for subsample in self.subsamples
            if not subsample.fastq_dirs
        ]

        # TODO: Some aborted samples may not have fastq_dirs. Handle this case.
        if missing_fastq_subsamples:
            logging.error(
                f"The following subsamples of '{self.sample_id}' have no FASTQ directories: {', '.join(missing_fastq_subsamples)}. "
                f"Skipping..."
            )
            self.status = "failed"
            return  # Halt processing for this composite sample

        # Step 2: Collect features from subsamples
        features = [subsample.feature for subsample in self.subsamples]
        features = list(set(features))

        # Step 3: Get library_prep_method
        library_prep_method = self.project_info.get("library_prep_method")

        # Step 4: Determine the pipeline and additional files required
        pipeline_info = self.get_pipeline_info(library_prep_method, features)
        if not pipeline_info:
            logging.error(f"No pipeline information found for sample {self.sample_id}")
            self.status = "failed"
            return

        pipeline = pipeline_info.get("pipeline")
        additional_files = pipeline_info.get("additional_files", [])

        logging.info(f"Pipeline: {pipeline}")
        logging.info(f"Additional files: {additional_files}")

        # Step 5: Generate necessary files
        logging.info(
            f"Generating additional files for composite sample {self.sample_id}"
        )

        if "libraries" in additional_files:
            self.generate_libraries_csv()
        if "hash_ref" in additional_files:
            self.generate_feature_reference_csv()
        if "multi" in additional_files:
            self.generate_multi_sample_csv()

        self.status = "processing"

    def get_pipeline_info(self, library_prep_method, features):
        for entry in self.decision_table:
            if entry["library_prep_method"] == library_prep_method and set(
                entry["features"]
            ) == set(features):
                return entry
        return None

    def generate_libraries_csv(self):
        logging.info(f"Generating library CSV for composite sample {self.sample_id}")
        library_csv_path = (
            self.file_handler.base_dir / f"{self.sample_id}_libraries.csv"
        )
        with open(library_csv_path, "w", newline="") as csvfile:
            writer = csv.DictWriter(
                csvfile, fieldnames=["fastqs", "sample", "library_type"]
            )
            writer.writeheader()
            for subsample in self.subsamples:
                feature_type = self.feature_to_library_type.get(subsample.feature)
                if not feature_type:
                    logging.error(
                        f"Feature type not found for feature '{subsample.feature}' in sample '{subsample.sample_id}'"
                    )
                    continue
                # Write one row per FASTQ directory
                for paths in subsample.fastq_dirs.values():
                    for path in paths:
                        writer.writerow(
                            {
                                "fastqs": str(path),
                                "sample": subsample.sample_id,
                                "library_type": feature_type,
                            }
                        )

    def generate_feature_reference_csv(self):
        logging.info(
            f"Generating feature reference CSV for composite sample {self.sample_id}"
        )
        pass

    def generate_multi_sample_csv(self):
        logging.info(
            f"Generating multi-sample CSV for composite sample {self.sample_id}"
        )
        pass


class TenXOriginalSample(TenXSampleBase):
    # decision_table = ConfigLoader().load_config("10x_decision_table.json")

    def __init__(
        self,
        sample_id,
        feature,
        sample_data,
        project_info,
        config,
        yggdrasil_db_manager,
    ):
        """
        Represents an original sample.

        Args:
            sample_id (str): ID of the original sample.
            sample_data (dict): Metadata related to the sample.
            project_info (dict): Metadata related to the parent project.
            config (dict): Configuration settings for the pipeline.
            yggdrasil_db_manager (YggdrasilDBManager): CouchDB manager instance for status tracking.
        """
        # Call the base class __init__
        super().__init__(sample_id, project_info, config, yggdrasil_db_manager)

        self.feature = feature
        self.sample_data = sample_data

    async def process(self):
        """
        Process the physical sample by handling its logical samples.
        """
        logging.info(
            f"Processing sample {self.sample_id} ({self.sample_data.get('customer_name', '')})"
        )

        # TODO: Correct below steps. Current step: Step 1

        # Step 1: Gather necessary information
        library_prep_method = self.project_info.get("library_prep_method")
        features = [self.feature]
        pipeline_info = self.get_pipeline_info(library_prep_method, features)
        if not pipeline_info:
            logging.error(f"No pipeline information found for sample {self.sample_id}")
            self.status = "failed"
            return

        pipeline_exec = pipeline_info.get("cellranger_exec")
        pipeline_cmd = pipeline_info.get("pipeline")
        additional_files = pipeline_info.get("additional_files", [])

        ref_genome = self.config.get("ref_genome")
        slurm_template_path = self.config.get("slurm_template_path")

        if not all([pipeline_info, ref_genome, slurm_template_path]):
            logging.error(
                "Missing configuration for cellranger path, reference genome, or Slurm template. Skipping..."
            )
            # TODO: distinguish between failed sample and yggdrasil derived failure
            self.status = "failed"
            # TODO: notify admin to check configuration (on Slack?)
            return

        # Collect FASTQ directories
        fastq_dirs = self.sample_data.get("fastq_dirs")
        if not fastq_dirs:
            logging.error(f"No FASTQ directories found for sample {self.sample_id}")
            self.status = "failed"
            return

        # Flatten the list of FASTQ paths
        fastq_paths = [str(path) for paths in fastq_dirs.values() for path in paths]

        # Step 2: Create arguments dictionary for the Slurm script
        args_dict = {
            "sample_id": self.sample_id,
            "cellranger_path": cellranger_path,
            "ref_genome": ref_genome,
            "fastq_paths": "\n".join(fastq_paths),
            "output_dir": str(self.file_handler.sample_dir),
            "sample_name": self.sample_id,
            # Add additional parameters if needed
        }

        # Step 3: Generate the Slurm script
        slurm_script_path = (
            self.file_handler.sample_dir / f"{self.sample_id}_cellranger_count.sh"
        )
        success = generate_slurm_script(
            args_dict, slurm_template_path, slurm_script_path
        )
        if not success:
            logging.error(
                f"Failed to generate Slurm script for sample {self.sample_id}"
            )
            self.status = "failed"
            return

        # Step 4: Submit the Slurm script
        try:
            subprocess.run(["sbatch", str(slurm_script_path)], check=True)
            logging.info(f"Submitted Slurm job for sample {self.sample_id}")
            self.status = "submitted"
        except subprocess.CalledProcessError as e:
            logging.error(
                f"Failed to submit Slurm job for sample {self.sample_id}: {e}"
            )
            self.status = "failed"
            return

        self.status = "processing"


class TenXSubsample:
    config = ConfigLoader().load_config("10x_config.json")

    def __init__(self, sample_id, feature, sample_data, project_info):
        """
        Initialize a PhysicalSample instance.

        Args:
            sample_id (str): ID of the physical sample (e.g. X3_24_025).
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
            if "library_prep" in self.sample_data:
                for prep_info in self.sample_data["library_prep"].values():
                    flowcell_ids.extend(prep_info.get("sequenced_fc", []))

            if not flowcell_ids:
                logging.warning(
                    f"No valid flowcells found for sample {self.sample_id}."
                )
            return flowcell_ids
        except Exception as e:
            logging.error(
                f"Error while fetching flowcell IDs for sample '{self.sample_id}': {e}",
                exc_info=True,
            )
            return None

    def locate_fastq_dirs(self):
        """
        Locate the parent directories of the FASTQ files for each flowcell.

        Returns:
            dict: A dictionary mapping flowcell IDs to their respective parent directories.
        """
        fastq_dirs = {}
        for flowcell_id in self.flowcell_ids:
            pattern = Path(
                self.config["seq_root_dir"],
                self.project_info.get("project_id", ""),
                self.sample_id,
                "*",
                flowcell_id,
            )
            fastq_dir = glob.glob(str(pattern))

            if fastq_dir:
                fastq_dirs[flowcell_id] = fastq_dir
            else:
                logging.warning(
                    f"No FASTQ directory found for flowcell {flowcell_id} in sample {self.sample_id}"
                )

        if not fastq_dirs:
            logging.warning(f"No FASTQ directories found for sample {self.sample_id}.")
            return None

        return fastq_dirs

    # def generate_library_csv(self):
    #     """
    #     Generate a combined library.csv file for the physical sample, containing all logical samples.
    #     """
    #     library_csv = Path(f"{self.sample_id}_library.csv")
    #     with open(library_csv, 'w') as f:
    #         f.write("fastqs,sample,library_type\n")
    #         for subsample in self.subsamples:
    #             # Each logical sample contributes its own data
    #             assay = subsample.assay
    #             fastqs = subsample.get_fastqs()  # Assume each logical sample has a method to retrieve fastq paths
    #             f.write(f"{fastqs},{subsample.sample_id},{assay}\n")
    #     return library_csv

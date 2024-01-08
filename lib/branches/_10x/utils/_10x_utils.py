# import logging

# from lib.utils.config_loader import ConfigLoader

# def collect_meta_per_sample(doc):
#     try:
#         config = ConfigLoader().load_config_path("lib/branches/_10x/10x_config.json")

#         project_method = doc["details"]["library_prep_option"]
#         ref_path = config["species_mappings"][project_method][doc["reference_genome"]]
#         cellranger_path = config["cellranger_path"][project_method]
#         sequenced_fc_root = config["seq_root_dir"]

#         samples = {}

#         for sample_name, sample_info in doc["samples"].items():
#             args_dict = {
#                 "project_name": doc['project_name'].replace(".", "__"),
#                 "customer_name": sample_info['details']['customer_name'],
#                 "comma_separated_fastq_file_paths": "",
#                 "ref_genome_path": ref_path,
#                 "cellranger_path": cellranger_path,
#                 "scilife_name": sample_name
#             }
            
#             for prep_id, prep_info in sample_info.get('library_prep', {}).items():
#                 print(prep_id, prep_info)
#                 for sequenced_fc in prep_info.get('sequenced_fc', []):
#                     print(sequenced_fc)
#                     fastq_path = f"{sequenced_fc_root}/{sequenced_fc}/Demultiplexing/{doc['project_name']}/Sample_{sample_name}"
#                     args_dict["comma_separated_fastq_file_paths"] += f"{fastq_path},"

#             args_dict["comma_separated_fastq_file_paths"] = args_dict["comma_separated_fastq_file_paths"].rstrip(',')

#             samples[sample_name] = args_dict

#     except Exception as e:
#         logging.warning(f"10x GEX: Error while collecting meta values: {e}")

#     return samples


import logging
from lib.utils.config_loader import ConfigLoader


def compile_metadata(metadata, sample_name, project_info, config):
    """
    Collect and transform metadata for a given sample.

    Args:
        metadata (dict): The sample metadata to be compiled.
        sample_name (str): The name or identifier of the sample.
        project_info (dict): Project-related information.
        config (dict): Pre-loaded method configurations.

    Returns:
        dict: A dictionary containing metadata for the specified sample.
    """
    try:
        # Initialize the dictionary to store arguments for the sample
        args_dict = {
            "project_name": project_info['project_name'],
            "customer_name": metadata.get('customer_name', ''),
            "scilife_name": metadata.get('scilife_name', ''),
            "comma_separated_fastq_file_paths": "",
            "ref_genome_path": config['species_mappings'][project_info['library_prep_option']][project_info['ref_genome']],
            "cellranger_path": config['cellranger_path'][project_info['library_prep_option']],
        }

        # Process library_prep information for the sample
        for prep_id, prep_info in metadata.get('library_prep', {}).items():
            # Iterate over the available sequenced flowcells
            for sequenced_fc in prep_info.get('sequenced_fc', []):
                # TODO: Validate that the fastq files exist
                fastq_path = f"{config['seq_root_dir']}/{sequenced_fc}/Demultiplexing/{project_info['project_name']}/Sample_{sample_name}"
                args_dict["comma_separated_fastq_file_paths"] += f"{fastq_path},"

        # Remove trailing comma from the FASTQ paths
        args_dict["comma_separated_fastq_file_paths"] = args_dict["comma_separated_fastq_file_paths"].rstrip(',')

        # Check for missing values in the sample level metadata
        if not all(args_dict.values()):
            logging.warning(f"Missing values for sample {sample_name}. Skipping metadata collection.")
            return None

        return args_dict

    except Exception as e:
        logging.warning(f"Error occurred while collecting metadata for sample '{sample_name}': {e}", exc_info=True)
        return None


def collect_meta_per_sample(doc):
    """
    Collect metadata for each sample based on the provided document.

    Args:
        doc (dict): The document containing information about the project and samples.

    Returns:
        dict or None: A dictionary containing metadata for each sample or None if collection is incomplete.
    """
    samples = {}

    try:
        # Load the 10x configuration
        config = ConfigLoader().load_config_path("lib/branches/_10x/10x_config.json")

        # Get the required values from the config
        project_method = doc["details"]["library_prep_option"]
        ref_path = config["species_mappings"][project_method].get(doc["reference_genome"])
        cellranger_path = config["cellranger_path"].get(project_method)
        sequenced_fc_root = config["seq_root_dir"]

        # Check for missing values in the project level metadata
        if not all([ref_path, cellranger_path, sequenced_fc_root]):
            missing_values = [key for key, value in {"ref_path": ref_path, "cellranger_path": cellranger_path, "sequenced_fc_root": sequenced_fc_root}.items() if not value]
            logging.warning(f"Missing values for {doc['project_name']}: {missing_values}. Skipping metadata collection.")
            return None

        # Create a dictionary to store arguments for each sample
        for sample_name, sample_info in doc.get("samples", {}).items():
            args_dict = {
                "project_name": doc['project_name'].replace(".", "__"),
                "customer_name": sample_info['details'].get('customer_name', ''),
                "comma_separated_fastq_file_paths": "",
                "ref_genome_path": ref_path,
                "cellranger_path": cellranger_path,
                "scilife_name": sample_name
            }

            # Iterate over library_prep information for the current sample
            for prep_id, prep_info in sample_info.get('library_prep', {}).items():
                # Iterate over the available sequenced flowcells for the current library_prep
                for sequenced_fc in prep_info.get('sequenced_fc', []):
                    # Create a path to the fastq files for the current sequenced flowcell
                    fastq_path = f"{sequenced_fc_root}/{sequenced_fc}/Demultiplexing/{doc['project_name']}/Sample_{sample_name}"
                    args_dict["comma_separated_fastq_file_paths"] += f"{fastq_path},"

            # Remove trailing comma from the FASTQ paths
            args_dict["comma_separated_fastq_file_paths"] = args_dict["comma_separated_fastq_file_paths"].rstrip(',')

            # Check for missing values in the sample level metadata
            if not all(args_dict.values()):
                logging.warning(f"Missing values for sample {doc['project_name']} - {sample_name}. Skipping metadata collection.")
                continue

            samples[sample_name] = args_dict

        return samples

    except Exception as e:
        # Log a warning and return None if there is an error collecting metadata.
        # This ensures that the function gracefully handles unexpected errors
        # and provides a clear warning in the log for further investigation.
        logging.warning(f"Error occurred while collecting metadata for 10x GEX: {e}")
        return None

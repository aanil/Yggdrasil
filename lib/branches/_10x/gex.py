import logging

# from lib.branches.branch_utils.genome_mapper import GenomeMapper
from lib.utils.slurm_utils import generate_slurm_script
from lib.branches._10x.utils._10x_utils import collect_meta_per_sample

def process(doc):    
    # mapper = GenomeMapper(_10x_config["species_mappings"])
    try:
        samples = collect_meta_per_sample(doc)

        for sample_name, sample in samples.items():
            output_file = f"sim_out/10x/{sample_name}_slurm_script.sh"
            generate_slurm_script(sample, "sim_out/10x/slurm_template.sh", output_file)


    except KeyError as e:
        logging.warning(f"GEX: Error while processing couchDB data: {e}")
    pass
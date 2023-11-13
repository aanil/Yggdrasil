import logging

from pathlib import Path

from lib.utils.config_loader import ConfigLoader 
# from lib.utils.config_utils import load_json_config
from lib.utils.slurm_utils import generate_slurm_script
from lib.utils.couch_utils import has_required_fields
from lib.branches.smartseq3.utils.ss3_utils import form_project_path
from lib.branches.smartseq3.utils.yaml_utils import write_yaml

def process(doc):
    """
    Process Smart-seq3 task based on the CouchDB doc document.

    Args:
        doc: The CouchDB doc document for the task.
    """
    # Implement SmartSeq 3-specific logic here
    logging.info("Here we are! SmartSeq 3")

    # Use this to skip running if working on other modules
    if doc:
        return None

    # ss3_config = load_json_config("ss3_config.json", "lib/branches/smartseq3/")
    ss3_config = ConfigLoader().load_config_path("lib/branches/smartseq3/ss3_config.json")

    if has_required_fields(doc, ss3_config["required_fields"]):
        logging.info("Has required fields!")

        # TODO: Here and below is a copy from the tests. Clean or put in functions if needed
        pid = doc['project_id']
        ilab_id = doc['details']['customer_project_reference']
        project_name = doc['project_name']

        ss3_root = ss3_config["smartseq3_dir"]
        seq_root = ss3_config["seq_root_dir"]
        project_path = form_project_path(project_name, pid, ss3_root)
    
        info_per_plate = []
        for sample_id, _ in doc['samples'].items():

            barcode = doc['samples'][sample_id]['library_prep']['A']['barcode']
            barcode = barcode.split('-')[-1]

            bc_path = ss3_root + '/' + 'barcodes' + '/' + barcode + '.txt'


            try:
                for key, val in doc['staged_files'][sample_id].items():
                    read = key.split('/')[-1].split('_')[3]

                    # Form the seq file paths
                    if 'R1' in  read:
                        r1fp = seq_root + '/' + key
                    elif 'R2' in read:
                        r2fp = seq_root + '/' + key
                    elif 'I1' in read:
                        i1fp = seq_root + '/' + key
                    elif 'I2' in read:
                        i2fp = seq_root + '/' + key
                    else:
                        print(f"Unexpected name in: {key}")
            except KeyError as e:
                # TODO: Could Slack alert this
                print(f"KeyError: No fastq files for {e} ({ilab_id})")
                continue


            info_per_plate.append({'sample_id': sample_id,
                                    'plate': doc['samples'][sample_id]['customer_name'],
                                    'bc_file': bc_path,
                                    'fastqs': {'R1': r1fp, 'R2': r2fp, 'I1': i1fp, 'I2': i2fp}})

        seq_setup = doc['details']['sequencing_setup'].split('-')
        r1 = seq_setup[0]
        i1 = seq_setup[1]
        i2 = seq_setup[2]
        r2 = seq_setup[3]
    
        ref_gen = doc['reference_genome']
        if not ref_gen:
            ref_gen = doc['details']['reference_genome']
    
        species = ref_gen.split(' ')[0]
        ref = ref_gen.split(' ')[-1][:-1]
    
        base_def_f1 = (f"cDNA(23-{r1})", "UMI(12-19)")
        base_def_f2 = f"cDNA(1-{r2})"
        base_def_f3 = f"BC(1-{i1})"
        base_def_f4 = f"BC(1-{i2})"


        for sample in info_per_plate:
            sample_id = sample['sample_id']
            to_yaml[sample_id] = sample
            to_yaml[sample_id]['ilab_id'] = ilab_id
            to_yaml[sample_id]['read_setup'] = {}
            to_yaml[sample_id]['read_setup']['R1'] = base_def_f1
            to_yaml[sample_id]['read_setup']['R2'] = base_def_f2
            to_yaml[sample_id]['read_setup']['I1'] = base_def_f3
            to_yaml[sample_id]['read_setup']['I2'] = base_def_f4

            # Form the output dir path. doc if you want the sample id instead of the plate id
            to_yaml[sample_id]['outdir'] = ss3_root + '/' + ilab_id + '/' + to_yaml[sample_id]['plate']

            to_yaml[sample_id]['ref'] = {}
            try:
                to_yaml[sample_id]['ref']['gen_path'] = ss3_config['gen_refs'][species.lower()]['idx_path']
                to_yaml[sample_id]['ref']['gtf_path'] = ss3_config['gen_refs'][species.lower()]['gtf_path']
            except KeyError as e:
                print(f"Reference for {e} species not found. Handle {sample_id} ({ilab_id}) manually!")
                to_yaml = None
                continue

            # TODO: Make sure all the folders exist and if not create them. Must be already solved in the ss3_tools repo
            to_yaml[sample_id]['out_yaml'] = Path(ss3_root + '/' + ilab_id + '/' + to_yaml[sample_id]['plate'] + '.yaml')

        config = {}
        config["file_paths"] = {}
        # TODO: Read this from a config file
        config["file_paths"]["yaml_template"] = '/home/anastasios/Documents/experiments/couch_db_to_yaml_ss3/templates/template.yaml'

        if to_yaml:
            for sample in to_yaml:
                write_yaml(config, to_yaml[sample])

        for sample in to_yaml:
            slurm_args = {"job_name": f"{to_yaml[sample]['ilab_id']}_{to_yaml[sample]['plate']}",
                        "yaml_filepath": to_yaml[sample]['out_yaml']}
            
            # TODO: Read this from a config file
            slurm_template_path = '/home/anastasios/Documents/experiments/couch_db_to_yaml_ss3/templates/ss3_template.sh'
            outpath = Path(ss3_root + '/' + ilab_id + '/' + to_yaml[sample]['plate'] + '.sh')

            generate_slurm_script(slurm_args, slurm_template_path, outpath)
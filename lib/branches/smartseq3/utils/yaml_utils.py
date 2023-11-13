from pathlib import Path
from ruamel.yaml import YAML

yaml=YAML()
yaml.preserve_quotes = True


def parse_yaml(config):
    yaml_template = Path(config["file_paths"]["yaml_template"])
    return yaml.load(yaml_template)


def write_yaml(config, args):
    template = parse_yaml(config)
    
    # print(template)
    template['project'] = args['plate']
    template['sequence_files']['file1']['name'] = str(args['fastqs']['R1'])
    template['sequence_files']['file2']['name'] = str(args['fastqs']['R2'])
    template['sequence_files']['file3']['name'] = str(args['fastqs']['I1'])
    template['sequence_files']['file4']['name'] = str(args['fastqs']['I2'])

    # Define the base definition according to read setup
    template['sequence_files']['file1']['base_definition'][0] = args['read_setup']['R1'][0]
    template['sequence_files']['file1']['base_definition'][1] = args['read_setup']['R1'][1]
    template['sequence_files']['file2']['base_definition'][0] = args['read_setup']['R2']
    template['sequence_files']['file3']['base_definition'] = args['read_setup']['I1']
    template['sequence_files']['file4']['base_definition'] = args['read_setup']['I2']

    template['reference']['STAR_index'] = str(args['ref']['gen_path'])
    template['reference']['GTF_file'] = str(args['ref']['gtf_path'])
    template['out_dir'] = str(args['outdir'])
    template['barcodes']['barcode_file'] = str(args['bc_file'])

    # project_path = Path(config["abs_paths"]["project_dir"].format(args["project_id"]))

    # # Check if project dir exists, otherwise create it
    # project_path.mkdir(exist_ok=True)
    # out_yaml = project_path / f"{args['plate']}.yaml"

    # TODO: Do not exit. Notify user (through Slack?).
    if args["out_yaml"].is_file():
        print(f"YAML file `{args['out_yaml'].name}` already exists.")
        print(f"Path: {args['out_yaml']}")
        print("Continuing to overwrite the file...")
        # print("Exiting... Please, resolve the issue manually.")
        # sys.exit(-1)

    with open(args["out_yaml"], 'w') as outfile:
        yaml.dump(template, outfile)

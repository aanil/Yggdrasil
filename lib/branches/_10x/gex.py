import logging

from lib.utils.config_loader import ConfigLoader
from lib.utils.couch_utils import has_required_fields

def process(doc):
    print("Processing 10x GEX")
    # Collect metadata
    
    # _10x_config = load_json_config("10x_config.json", "lib/branches/_10x/")
    _10x_config = ConfigLoader().load_config_path("lib/branches/_10x/10x_config.json")

    if has_required_fields(doc, _10x_config["required_fields"]):
        try:
            # Gather project_id(P...), project_name(O.Karlsson...)[needs formating], no_of_samples, [samples.<sample>.library_prep.<X>.sequenced_fc[]]
            # details.customer_project_reference, samples.<sample>.customer_name(10X_...), samples.<sample>.scilife_name(P..._...), reference_genome
            pid = doc['project_id']
            pname = doc['project_name']
            iname = doc['details']['customer_project_reference']

            ref_gen = doc['reference_genome']
            # TODO: It will never get here if the previous line fails. Handle accordingly
            if not ref_gen:
                ref_gen = doc['details']['reference_genome']

            info_per_sample = []

            for sample_id, _ in doc['samples'].items():
                escg_sample_id = doc['samples'][sample_id]['customer_name']

                flowcells = set()

                for prep in doc['samples'][sample_id]['library_prep'].items():
                    flowcells.update(set(doc['samples'][sample_id]['library_prep'][prep]['sequenced_fc']))

                info_per_sample.append({'sample_id': sample_id,
                                        'escg_sample_id': escg_sample_id,
                                        'flowcells': flowcells})


        except KeyError as e:
            logging.warning(f"Error while processing incoming couchDB data: {e}")
        pass
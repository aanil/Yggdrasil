from lib.utils.logging_utils import custom_logger

logging = custom_logger(__name__.split('.')[-1])

def generate_slurm_script(args_dict, template_fpath, output_fpath):
    """
    Generate a Slurm batch script by filling in placeholders in a template.

    This function reads a Slurm script template, replaces placeholders with 
    values provided in `args_dict`, and writes the resulting script to `output_fpath`.

    Args:
        args_dict (dict): A dictionary of arguments and their values to be
            inserted into the template.
        template_fpath (str): The filepath to the Slurm script template.
        output_fpath (str): The filepath where the generated Slurm script
            will be saved.

    Returns:
        bool: True if the script is successfully written, False otherwise.
    """
    try:
        with open(template_fpath, "r") as template_file:
            template = template_file.read()

        script_content = template.format(**args_dict)

        with open(output_fpath, "w") as script_file:
            script_file.write(script_content)

        logging.debug(f"Slurm script generated successfully at {output_fpath}")
        return True
    except Exception as e:
        logging.error(f"Failed to generate Slurm script: {e}")
        return False

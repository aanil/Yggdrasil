

def generate_slurm_script(args_dict, template_fpath, output_fpath):
    """
    Generate a Slurm batch script by filling in placeholders in a template.

    Args:
        args_dict (dict): A dictionary of arguments and their values to be
            inserted into the template. Each key in the dictionary corresponds
            to a placeholder in the template, and the associated value is used
            as its replacement.

        template_filepath (str): The filepath to the Slurm script template.
            The template should contain placeholders enclosed in curly braces,
            e.g., "{job_name}".

        output_filepath (str): The filepath where the generated Slurm script
            will be saved.

    Returns:
        None: This function only generates and saves the Slurm script.

    Example:
        To generate a Slurm script from a template file, you can call the
        function as follows:

        >>> args = {
        ...     "job_name": "test_batch",
        ...     "yaml_filepath": "/home/user/path/to.yaml",
        ...     # Add more arguments as needed
        ... }
        >>> generate_slurm_script(args, "slurm_template.sh", "slurm_script.sh")

    """
    # Read the Slurm script template from the specified file
    with open(template_fpath, "r") as template_file:
        template = template_file.read()

    # Fill in the template with the provided arguments
    script_content = template.format(**args_dict)

    # Write the generated script to the specified output file
    with open(output_fpath, "w") as script_file:
        script_file.write(script_content)
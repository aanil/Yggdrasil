import os
import logging
import importlib

from pathlib import Path

class YggdrasilUtilities:
    """
    Utility class for common functions in the Yggdrasil project.

    This class provides a collection of utility functions used across
    various modules in the Yggdrasil project. It includes functions
    for handling configurations, loading modules, and other common tasks.

    Attributes:
        module_cache (dict): A cache for loaded modules and classes.
        CONFIG_DIR (Path): The directory containing configuration files.

    Methods:
        get_path(file_name: str) -> Path:
            Get the full path to a specific configuration or setup file
            for the Yggdrasil application.

        load_realm_class(module_path: str) -> type:
            Load a realm class from a module path and cache it for reuse.

        load_module(module_path: str) -> module:
            Load a module and cache it for reuse.

        env_variable(variable_name: str, default=None) -> str or None:
            Get the value of an environment variable.

    Usage:
        # Example Usage:
        utils = YggdrasilUtilities()
        config_path = utils.get_path("my_config.json")
        username = utils.env_variable("USERNAME")
    """
    module_cache = {}
    CONFIG_DIR = Path(__file__).parent.parent.parent / "yggdrasil_workspace/common/configurations"

    @staticmethod
    def load_realm_class(module_path):
        """
        Load a realm class from a module path and cache it for reuse. The module path should include
        the full path to the class in the format 'module.submodule.ClassName'.

        Args:
            module_path (str): The full path of the realm class to load (including the class name).

        Returns:
            type: The loaded realm class, or None if loading fails.
        """
        if module_path in YggdrasilUtilities.module_cache:
            return YggdrasilUtilities.module_cache[module_path]

        try:
            # Split the module path to get the module and class name
            module_name, class_name = module_path.rsplit('.', 1)
            module = importlib.import_module(module_name)
            realm_class = getattr(module, class_name)
            YggdrasilUtilities.module_cache[module_path] = realm_class
            return realm_class
        except (ImportError, AttributeError) as e:
            logging.error(f"Failed to load realm class from '{module_path}': {e}")
            return None

    @staticmethod
    def load_module(module_path):
        """
        Load a module and cache it for reuse.

        Args:
            module_path (str): The path of the module to load.

        Returns:
            module: The loaded module, or None if loading fails.
        """
        if module_path in YggdrasilUtilities.module_cache:
            return YggdrasilUtilities.module_cache[module_path]

        try:
            task_module = importlib.import_module(module_path)
            YggdrasilUtilities.module_cache[module_path] = task_module
            return task_module
        except ImportError as e:
            logging.error(f"Failed to load module '{module_path}': {e}")
            return None
        

    @staticmethod
    def get_path(file_name):
        """
        Get the full path to a specific configuration file for the Yggdrasil
        application from the centralized configurations directory.

        Args:
            file_name (str): The name of the configuration file.

        Returns:
            Path: A Path object representing the full path to the specified
                configuration file, or None if the file is not found.
        """
        # Get the path to the configuration file
        config_file = YggdrasilUtilities.CONFIG_DIR / file_name

        if config_file.exists():
            return config_file
        else:
            logging.error(f"Configuration file '{file_name}' not found.")
            return None


    @staticmethod
    def env_variable(variable_name, default=None):
        """
        Get the value of an environment variable.

        Args:
            variable_name (str): The name of the environment variable.
            default: A default value to return if the environment variable is not set.

        Returns:
            str or None: The value of the environment variable or the default value.
        """
        return os.environ.get(variable_name, default)


######### TODO: POTENTIALLY MOVE FUNCTIONS BELOW TO A SEPARATE UTILITIES CLASS ##################

    def check_project_exists(project_id: str) -> bool:
        from lib.couchdb.manager import YggdrasilDBManager
        db_manager = YggdrasilDBManager()
        existing_document = db_manager.get_document_by_project_id(project_id)
        if existing_document:
            logging.info(f"Project with ID {project_id} exists.")
            return existing_document
        else:
            logging.info(f"Project with ID {project_id} does not exist.")
            return None
        
    def create_project(project_id: str, projects_reference: str, method: str): # -> YggdrasilDocument:
        from lib.couchdb.manager import YggdrasilDBManager
        db_manager = YggdrasilDBManager()
        new_document = db_manager.create_project(project_id, projects_reference, method)
        logging.info(f"New project with ID {project_id} created successfully.")
        return new_document
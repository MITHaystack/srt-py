"""yaml_tools.py

Module Containing Brief Functions for Validating and Parsing YAML

"""
import yamale
import yaml

from pathlib import Path

schema_file_name = "schema.yaml"
config_file_name = "config.yaml"
root_folder = Path(__file__).parent.parent


def validate_yaml_schema(path="config"):
    """Validates YAML Config File Against Schema

    Parameters
    ----------
    path : str
        Name / Path of the Folder from Root Directory

    Returns
    -------
    bool
        If the Yamale Validates Properly
    """
    schema = yamale.make_schema(Path(root_folder, path, schema_file_name))
    data = yamale.make_data(Path(root_folder, path, config_file_name))
    return yamale.validate(schema, data)


def load_yaml(path="config"):
    """Parses

    Parameters
    ----------
    path : str
        Name / Path of the Folder from Root Directory

    Returns
    -------
    config : dict
        Dictionary containing configuration info
    """
    with open(Path(root_folder, path, config_file_name)) as file:
        # The FullLoader parameter handles the conversion from YAML
        # scalar values to Python the dictionary format
        config = yaml.load(file, Loader=yaml.FullLoader)
        return config

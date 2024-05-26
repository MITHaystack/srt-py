"""config_loader.py

Module Containing Brief Functions for Validating and Parsing YAML

"""

import yamale
import yaml


def validate_yaml_schema(config_path, schema_path):
    """Validates YAML Config File Against Schema

    Parameters
    ----------
    config_path : str
        Name / Path to the config.yaml File
    schema_path : str
        Name / Path to the schema.yaml File

    Returns
    -------
    bool
        If the Yamale Validates Properly
    """
    schema = yamale.make_schema(schema_path)
    data = yamale.make_data(config_path)
    return yamale.validate(schema, data)


def load_yaml(config_path):
    """Parses

    Parameters
    ----------
    config_path : str
        Name / Path to the config.yaml File

    Returns
    -------
    config : dict
        Dictionary containing configuration info
    """
    with open(config_path) as file:
        # The FullLoader parameter handles the conversion from YAML
        # scalar values to Python the dictionary format
        config = yaml.load(file, Loader=yaml.FullLoader)
        return config

import yamale
import yaml

from os.path import join

schema_file_name = 'schema.yaml'
config_file_name = 'config.yaml'


def validate_yaml_schema(path="../config/"):
    """

    :param path:
    :return:
    """
    schema = yamale.make_schema(join(path, schema_file_name))
    data = yamale.make_data(join(path, config_file_name))
    return yamale.validate(schema, data)


def load_yaml(path="../config/"):
    """

    :param path:
    :return:
    """
    with open(join(path, config_file_name)) as file:
        # The FullLoader parameter handles the conversion from YAML
        # scalar values to Python the dictionary format
        config = yaml.load(file, Loader=yaml.FullLoader)
        return config

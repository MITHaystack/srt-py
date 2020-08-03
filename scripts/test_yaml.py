"""test_yaml.py

Validates and Prints the YAML Dictionary

"""
from srt.daemon.utilities.yaml_tools import validate_yaml_schema, load_yaml

if __name__ == "__main__":
    validate_yaml_schema()
    print(load_yaml())

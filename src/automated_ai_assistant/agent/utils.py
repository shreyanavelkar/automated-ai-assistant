import os

import yaml

file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'utils', 'openai.yml'))


def load_api_key():
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config['openai']['key']

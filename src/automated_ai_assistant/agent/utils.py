import yaml


def load_api_key():
    with open('openai.yml', 'r') as file:
        config = yaml.safe_load(file)
    return config['openai']['key']

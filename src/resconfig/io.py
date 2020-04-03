from . import json
from . import yaml


class IO:
    def load_from_json(self, filename):
        with open(filename) as f:
            loaded = json.load(f)
        self.replace(loaded)

    def load_from_yaml(self, filename):
        with open(filename) as f:
            loaded = yaml.load(f)
        self.replace(loaded)

    def save_to_json(self, filename):
        with open(filename, "w") as f:
            json.dump(self.asdict(), f)

    def save_to_yaml(self, filename):
        with open(filename, "w") as f:
            yaml.dump(self.asdict(), f)

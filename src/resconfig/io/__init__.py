from pathlib import Path

from . import ini
from . import json
from . import yaml


def _suffix_to_filetype(filename):
    filetype = {".ini": "ini", ".yaml": "yaml", ".yml": "yaml", ".json": "json"}.get(
        Path(filename).suffix, "ini"
    )
    return filetype


class IO:
    def __load(self, filename, filetype=None):
        load = {"ini": ini.load, "json": json.load, "yaml": yaml.load}.get(
            filetype, ini.load
        )
        with open(filename) as f:
            loaded = load(f)
        self.replace(loaded)

    def load(self, filename):
        self.__load(filename, _suffix_to_filetype(filename))

    def load_from_ini(self, filename):
        self.__load(filename, "ini")

    def load_from_json(self, filename):
        self.__load(filename, "json")

    def load_from_yaml(self, filename):
        self.__load(filename, "yaml")

    def __save(self, filename, filetype=None):
        dump = {"ini": ini.dump, "json": json.dump, "yaml": yaml.dump}.get(
            filetype, ini.dump
        )
        with open(filename, "w") as f:
            dump(self.asdict(), f)

    def save(self, filename):
        self.__save(filename, _suffix_to_filetype(filename))

    def save_to_ini(self, filename):
        self.__save(filename, "ini")

    def save_to_json(self, filename):
        self.__save(filename, "json")

    def save_to_yaml(self, filename):
        self.__save(filename, "yaml")

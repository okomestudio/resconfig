from pathlib import Path

from ..dicttype import Dict
from ..typing import List
from . import ini
from . import json
from . import toml
from . import yaml


def _suffix_to_filetype(filename):
    filetype = {
        ".ini": "ini",
        ".toml": "toml",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".json": "json",
    }.get(Path(filename).suffix, "ini")
    return filetype


class IO:
    def _load_as_dict(self, filename, filetype=None):
        if filetype is None:
            filetype = _suffix_to_filetype(filename)
        load = {
            "ini": ini.load,
            "json": json.load,
            "toml": toml.load,
            "yaml": yaml.load,
        }.get(filetype, ini.load)
        with open(filename) as f:
            loaded = load(f)
        return Dict(loaded)

    def __load(self, filename, filetype=None):
        loaded = self._load_as_dict(filename, filetype)
        self.replace(loaded)

    def load(self, filename):
        self.__load(filename, _suffix_to_filetype(filename))

    def load_from_ini(self, filename):
        self.__load(filename, "ini")

    def load_from_json(self, filename):
        self.__load(filename, "json")

    def load_from_toml(self, filename):
        self.__load(filename, "toml")

    def load_from_yaml(self, filename):
        self.__load(filename, "yaml")

    def __save(self, filename, filetype=None):
        dump = {
            "ini": ini.dump,
            "json": json.dump,
            "toml": toml.dump,
            "yaml": yaml.dump,
        }.get(filetype, ini.dump)
        with open(filename, "w") as f:
            dump(self.asdict(), f)

    def save(self, filename):
        self.__save(filename, _suffix_to_filetype(filename))

    def save_to_ini(self, filename):
        self.__save(filename, "ini")

    def save_to_json(self, filename):
        self.__save(filename, "json")

    def save_to_toml(self, filename):
        self.__save(filename, "toml")

    def save_to_yaml(self, filename):
        self.__save(filename, "yaml")

    def config_from_file(self, paths: List[str]) -> Dict:
        """Read the config from a file as a Dict.

        This method searches for the first existing file from the list.
        """
        dic = Dict()
        for path in paths:
            path = Path(path)
            if path.is_file():
                content = self._load_as_dict(path)
                dic.merge(content)
                break
        return dic

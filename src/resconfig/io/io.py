from copy import deepcopy
from enum import Enum
from pathlib import Path

from ..dicttype import Dict
from ..typing import FilePath
from ..typing import List
from ..typing import NewType
from ..typing import Optional
from . import ini
from . import json
from . import toml
from . import yaml


class FileType(Enum):
    ini = 1
    json = 2
    toml = 3
    yaml = 4


FileTypes = NewType("FileTypes", FileType)


def _suffix_to_filetype(filename: FilePath):
    filetype = {
        ".ini": FileType.ini,
        ".json": FileType.json,
        ".toml": FileType.toml,
        ".yaml": FileType.yaml,
        ".yml": FileType.yaml,
    }.get(Path(filename).suffix, FileType.ini)
    return filetype


class IO:
    def _read_as_dict(
        self, filename: FilePath, filetype: Optional[FileTypes] = None
    ) -> Dict:
        if filetype is None:
            filetype = _suffix_to_filetype(filename)
        load = {
            FileType.ini: ini.load,
            FileType.json: json.load,
            FileType.toml: toml.load,
            FileType.yaml: yaml.load,
        }.get(filetype, ini.load)
        with open(filename) as f:
            loaded = load(f)
        return Dict(loaded)

    def _read_from_files_as_dict(self, paths: List[FilePath]) -> Dict:
        """Read the config from a file as a Dict.

        This method searches for the first existing file from the list.
        """
        dic = Dict()
        for path in paths:
            path = Path(path)
            if path.is_file():
                content = self._read_as_dict(path)
                dic.merge(content)
                break
        return dic

    def __load(self, filename: FilePath, filetype=None):
        conf = deepcopy(self._default)
        loaded = self._read_as_dict(filename, filetype)
        conf.merge(loaded)
        self.replace(conf)

    def load(self, filename: FilePath):
        """Load config from the file.

        The file type is inferred from the filename extension."""
        self.__load(filename, _suffix_to_filetype(filename))

    def load_from_config_paths(self, paths: List[FilePath] = None):
        """Load config from the first existing file from the list.

        If the paths are not given, then it is loaded from the default config paths
        provided at the time of ResConfig instantiation, if any.
        """
        conf = deepcopy(self._default)
        config_paths = paths or self._config_paths
        if config_paths:
            conf.merge(self._read_from_files_as_dict(config_paths))
        if conf:
            self.replace(conf)

    def load_from_ini(self, filename: FilePath):
        """Load config from the INI file."""
        self.__load(filename, FileType.ini)

    def load_from_json(self, filename: FilePath):
        """Load config from the JSON file."""
        self.__load(filename, FileType.json)

    def load_from_toml(self, filename: FilePath):
        """Load config from the TOML file."""
        self.__load(filename, FileType.toml)

    def load_from_yaml(self, filename: FilePath):
        """Load config from the YAML file."""
        self.__load(filename, FileType.yaml)

    def __save(self, filename: FilePath, filetype: Optional[FileType] = None):
        dump = {
            FileType.ini: ini.dump,
            FileType.json: json.dump,
            FileType.toml: toml.dump,
            FileType.yaml: yaml.dump,
        }.get(filetype, ini.dump)

        d = deepcopy(self._conf)
        self._schema.unapply_all(d)

        with open(filename, "w") as f:
            dump(d, f)

    def save(self, filename: FilePath):
        """Save config to the file.

        The file type is inferred from the filename extension."""
        self.__save(filename, _suffix_to_filetype(filename))

    def save_to_ini(self, filename: FilePath):
        """Save config to the INI file."""
        self.__save(filename, FileType.ini)

    def save_to_json(self, filename: FilePath):
        """Save config to the JSON file."""
        self.__save(filename, FileType.json)

    def save_to_toml(self, filename: FilePath):
        """Save config to the TOML file."""
        self.__save(filename, FileType.toml)

    def save_to_yaml(self, filename: FilePath):
        """Save config to the YAML file."""
        self.__save(filename, FileType.yaml)

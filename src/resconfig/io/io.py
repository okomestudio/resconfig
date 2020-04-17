from copy import deepcopy
from enum import Enum
from pathlib import Path

from ..ondict import ONDict
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


def _suffix_to_filetype(filename: FilePath) -> FileType:
    filetype = {
        ".ini": FileType.ini,
        ".json": FileType.json,
        ".toml": FileType.toml,
        ".yaml": FileType.yaml,
        ".yml": FileType.yaml,
    }.get(Path(filename).suffix, FileType.ini)
    return filetype


class IO:
    """The mix-in to add file IO functionality."""

    def _read_as_dict(
        self, filename: FilePath, filetype: Optional[FileTypes] = None
    ) -> ONDict:
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
        return ONDict(loaded)

    def _read_from_files_as_dict(self, paths: List[FilePath]) -> ONDict:
        """Read the config from a file as a ONDict.

        This method searches for the first existing file from the list.
        """
        dic = ONDict()
        for path in paths:
            path = Path(path)
            if path.is_file():
                content = self._read_as_dict(path)
                dic.merge(content)
                break
        return dic

    def load_from_config_paths(self, paths: List[FilePath] = None):
        """Load config from the first existing file from the list.

        If the paths are not given, then it is loaded from the default config paths
        provided at the time of ResConfig instantiation, if any.
        """
        config_paths = paths or self._config_paths
        from_files = (
            [self._read_from_files_as_dict(config_paths)] if config_paths else None
        )
        if from_files:
            self.replace(self._prepare_config(from_files=from_files))

    def __update_from_file(self, filename: FilePath, filetype: FileType):
        self.update(self._read_as_dict(filename, filetype))

    def update_from_file(self, filename: FilePath):
        """Update config from the file.

        The file type is inferred from the filename extension.
        """
        self.__update_from_file(filename, _suffix_to_filetype(filename))

    def update_from_ini(self, filename: FilePath):
        """Update config from the INI file."""
        self.__update_from_file(filename, FileType.ini)

    def update_from_json(self, filename: FilePath):
        """Update config from the JSON file."""
        self.__update_from_file(filename, FileType.json)

    def update_from_toml(self, filename: FilePath):
        """Update config from the TOML file."""
        self.__update_from_file(filename, FileType.toml)

    def update_from_yaml(self, filename: FilePath):
        """Update config from the YAML file."""
        self.__update_from_file(filename, FileType.yaml)

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

    def save_to_file(self, filename: FilePath):
        """Save config to the file.

        The file type is inferred from the filename extension.
        """
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

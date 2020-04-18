from copy import deepcopy
from enum import Enum
from pathlib import Path

from ..ondict import ONDict
from ..typing import FilePath
from ..typing import List
from ..typing import NewType
from ..typing import Optional
from ..utils import experimental
from . import ini
from . import json
from . import toml
from . import yaml
from .utils import ensure_path


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


def _read_as_dict(filename: FilePath, filetype: Optional[FileTypes] = None) -> ONDict:
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


def read_from_files_as_dict(paths: List[FilePath], merge: bool = False) -> ONDict:
    """Read the config from a file(s) as an :class:`ONDict`.

    How the config is constructed depends on the ``merge`` flag. If :obj:`True`, the
    files are searched in the reverse order, and the configs are read from all existing
    files and merged in that order. If :obj:`False`, then the files are searched for in
    the order given in ``paths``, and the first existing file provides the config to be
    read (and the rest are ignored).

    Args:
        paths: A list of config file paths.
        merge: The flag for the merge mode; see the function description.

    Returns:
        An :class:`~resconfig.ondict.ONDict` object.
    """
    d = ONDict()
    paths = reversed(paths) if merge else paths
    for path in paths:
        path = ensure_path(path)
        if path.is_file():
            content = _read_as_dict(path)
            d.merge(content)
            if not merge:
                break
    return d


class IO:
    """The mix-in to add file IO functionality."""

    def update_from_files(self, paths: List[FilePath], merge=False):
        """Update config from files.

        How the config is constructed depends on the ``merge`` flag. If :obj:`True`, the
        files are searched in the reverse order, and the configs are read from all
        existing files and merged in that order. If :obj:`False`, then the files are
        searched for in the order given in ``paths``, and the first existing file
        provides the config to be read (and the rest are ignored).

        Args:
            paths: A list of config file paths.
            merge: The flag for the merge mode; see the function description.
        """
        self.update(read_from_files_as_dict(paths, merge))

    def __update_from_file(self, filename: FilePath, filetype: FileType):
        self.update(_read_as_dict(filename, filetype))

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

    @experimental
    def save_to_file(self, filename: FilePath):
        """Save config to the file.

        The file type is inferred from the filename extension.
        """
        self.__save(filename, _suffix_to_filetype(filename))

    @experimental
    def save_to_ini(self, filename: FilePath):
        """Save config to the INI file."""
        self.__save(filename, FileType.ini)

    @experimental
    def save_to_json(self, filename: FilePath):
        """Save config to the JSON file."""
        self.__save(filename, FileType.json)

    @experimental
    def save_to_toml(self, filename: FilePath):
        """Save config to the TOML file."""
        self.__save(filename, FileType.toml)

    @experimental
    def save_to_yaml(self, filename: FilePath):
        """Save config to the YAML file."""
        self.__save(filename, FileType.yaml)

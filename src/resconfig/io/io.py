from ..ondict import ONDict
from ..typing import FilePath
from ..typing import List
from ..utils import experimental
from .paths import ConfigPath
from .paths import INIPath
from .paths import JSONPath
from .paths import TOMLPath
from .paths import YAMLPath
from .utils import ensure_path


def read_from_files_as_dict(
    paths: List[FilePath], merge: bool = False, schema=None
) -> ONDict:
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
            if not isinstance(path, ConfigPath):
                path = ConfigPath.from_extension(path)
            content = path.load(schema)
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
        self.update(read_from_files_as_dict(paths, merge, self._default))

    def __update_from_file(self, filename: ConfigPath):
        self.update(filename.load(self._default))

    def update_from_file(self, filename: FilePath):
        """Update config from the file.

        The file type is inferred from the filename extension.
        """
        if not isinstance(filename, ConfigPath):
            filename = ConfigPath.from_extension(filename)
        self.__update_from_file(filename)

    def update_from_ini(self, filename: FilePath):
        """Update config from the INI file."""
        self.__update_from_file(INIPath(filename))

    def update_from_json(self, filename: FilePath):
        """Update config from the JSON file."""
        self.__update_from_file(JSONPath(filename))

    def update_from_toml(self, filename: FilePath):
        """Update config from the TOML file."""
        self.__update_from_file(TOMLPath(filename))

    def update_from_yaml(self, filename: FilePath):
        """Update config from the YAML file."""
        self.__update_from_file(YAMLPath(filename))

    def __save(self, filename: ConfigPath):
        filename.dump(self._conf, schema=self._default)

    @experimental
    def save_to_file(self, filename: FilePath):
        """Save config to the file.

        The file type is inferred from the filename extension.
        """
        if not isinstance(filename, ConfigPath):
            filename = ConfigPath.from_extension(filename)
        self.__save(filename)

    @experimental
    def save_to_ini(self, filename: FilePath):
        """Save config to the INI file."""
        self.__save(INIPath(filename))

    @experimental
    def save_to_json(self, filename: FilePath):
        """Save config to the JSON file."""
        self.__save(JSONPath(filename))

    @experimental
    def save_to_toml(self, filename: FilePath):
        """Save config to the TOML file."""
        self.__save(TOMLPath(filename))

    @experimental
    def save_to_yaml(self, filename: FilePath):
        """Save config to the YAML file."""
        self.__save(YAMLPath(filename))

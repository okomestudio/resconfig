from logging import getLogger
from pathlib import Path

from ..typing import FilePath
from . import ini
from . import json
from . import toml
from . import yaml

log = getLogger(__name__)


class ConfigPath(type(Path())):
    """Path for configuration file."""

    module = None

    def dump(self, conf, schema=None):
        with open(self, "w") as f:
            self.module.dump(conf, f, schema)

    def load(self, schema=None) -> "ONDict":
        with open(self) as f:
            return self.module.load(f, schema)

    @classmethod
    def from_extension(cls, filename: FilePath) -> "ConfigPath":
        t = {
            ".ini": INIPath,
            ".json": JSONPath,
            ".toml": TOMLPath,
            ".yaml": YAMLPath,
            ".yml": YAMLPath,
        }.get(Path(filename).suffix, INIPath)
        return t(filename)


class INIPath(ConfigPath):
    """Wrapper for INI config file path."""

    module = ini


class JSONPath(ConfigPath):
    """Wrapper for JSON file path."""

    module = json


class TOMLPath(ConfigPath):
    """Wrapper for TOML file path."""

    module = toml


class YAMLPath(ConfigPath):
    """Wrapper for YAML file path."""

    module = yaml

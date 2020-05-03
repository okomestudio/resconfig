from logging import getLogger
from pathlib import Path

from ..typing import FilePath
from ..typing import Optional
from . import ini
from . import json
from . import toml
from . import yaml

log = getLogger(__name__)


class ConfigPath(type(Path())):
    """Path for configuration file."""

    module = None

    def dump(self, conf: "ONDict", schema: Optional["ONDict"] = None):
        """Dump config to file at path.

        Args:
            conf: Configuration to dump.
            schema: Configuration schema.
        """
        with open(self, "w") as f:
            self.module.dump(conf, f, schema)

    def load(self, schema: Optional["ONDict"] = None) -> "ONDict":
        """Load config from file at path.

        Args:
            schema: Configuration schema.
        """
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

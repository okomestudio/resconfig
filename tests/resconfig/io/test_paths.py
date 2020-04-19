import pytest

from resconfig.io.paths import ConfigPath
from resconfig.io.paths import INIPath
from resconfig.io.paths import JSONPath
from resconfig.io.paths import TOMLPath
from resconfig.io.paths import YAMLPath


class TestConfigPath:
    @pytest.mark.parametrize(
        "name, ptype",
        [
            ("a", INIPath),
            ("a.ini", INIPath),
            ("a.json", JSONPath),
            ("a.toml", TOMLPath),
            ("a.yaml", YAMLPath),
            ("a.yml", YAMLPath),
        ],
    )
    def test_from_extension(self, name, ptype):
        assert isinstance(ConfigPath.from_extension(name), ptype)

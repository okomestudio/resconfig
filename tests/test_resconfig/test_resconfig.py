from unittest import mock

import pytest

from resconfig.resconfig import Action
from resconfig.resconfig import REMOVE
from resconfig.resconfig import ResConfig


@pytest.fixture
def default_config():
    yield {"a": 1, "b": {"c": 2}}


class TestResConfig:
    @pytest.fixture(scope="function", autouse=True)
    def setup(self, request, default_config):
        request.instance.default = default_config
        yield

    def test(self):
        config = ResConfig(self.default)
        assert config.get("b.c") == self.default["b"]["c"]

    def test_register(self):
        config = ResConfig(self.default)
        cb = mock.Mock()
        config.register("b.c", cb)
        config.update({"b": {"c": -1}})
        cb.assert_called_with(Action.MODIFIED, self.default["b"]["c"], -1)

    def test_register_with_dictval(self):
        config = ResConfig(self.default)
        cb = mock.Mock()
        config.register("b", cb)
        config.update({"b": {"d": 4}})
        cb.assert_called_with(Action.MODIFIED, self.default["b"], {"d": 4})

    def test_reloader(self):
        config = ResConfig(self.default)

        called = mock.Mock()

        @config.reloader("b")
        def reloader_func(*args, **kwargs):
            called(*args, **kwargs)

        assert reloader_func in config._reloaders["b"][config.reloaderkey]

        config.reload()
        called.assert_called_with(Action.RELOADED, self.default["b"], self.default["b"])

    def test_update(self):
        config = ResConfig(self.default)
        config.update({"b": {"d": -1}})
        assert config.get("b.d") == -1

    def test_update_delete_field(self):
        config = ResConfig(self.default)
        assert "a" in config._conf
        config.update({"a": REMOVE})
        assert "a" not in config._conf

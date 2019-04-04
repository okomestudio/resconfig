from unittest import mock

import pytest

from resconfig.resconfig import Action
from resconfig.resconfig import REMOVE
from resconfig.resconfig import ResConfig


@pytest.fixture
def default_config():
    yield {"a": 1, "b": {"c": 2}}


@pytest.fixture
def rc(default_config):
    yield ResConfig(default_config)


class TestCase:
    @pytest.fixture(scope="function", autouse=True)
    def setup(self, request, default_config):
        request.instance.default = default_config
        yield


class TestReloadable(TestCase):
    def test_deregister_from_nonexisting_key(self, rc):
        with pytest.raises(KeyError):
            rc.deregister("b.c")

    def test_deregister_nonexisting_reloader(self, rc):
        rc.register("b.c", lambda *args: args)
        with pytest.raises(ValueError):
            rc.deregister("b.c", lambda *args: args)

    def test_deregister_all(self, rc):
        def f(*args):
            return args

        rc.register("b.c", f)
        rc.deregister("b.c")
        with pytest.raises(KeyError):
            rc.deregister("b.c", f)

    def test_deregister_last_reloader(self, rc):
        def f(*args):
            return args

        rc.register("b.c", f)
        rc.deregister("b.c", f)
        with pytest.raises(KeyError):
            rc.deregister("b.c", f)

    def test_register(self, rc):
        cb = mock.Mock()
        rc.register("b.c", cb)
        rc.update({"b": {"c": -1}})
        cb.assert_called_with(Action.MODIFIED, self.default["b"]["c"], -1)

    def test_register_with_dictval(self, rc):
        cb = mock.Mock()
        rc.register("b", cb)
        rc.update({"b": {"d": 4}})
        cb.assert_called_with(Action.MODIFIED, self.default["b"], {"d": 4})

    def test_reload(self, rc):
        called = mock.Mock()

        @rc.reloader("b")
        def reloader_func(*args, **kwargs):
            called(*args, **kwargs)

        assert reloader_func in rc._reloaders["b"][rc.reloaderkey]

        rc.reload()
        called.assert_called_with(Action.RELOADED, self.default["b"], self.default["b"])


class TestGet(TestCase):
    def test(self, rc):
        assert rc.get("b.c") == self.default["b"]["c"]

    def test_default(self, rc):
        assert rc.get("non", "default") == "default"

    def test_without_default(self, rc):
        with pytest.raises(KeyError):
            rc.get("non")


class TestLoad(TestCase):
    pass


class TestUpdate(TestCase):
    def test_keys_with_dict_notation(self, rc):
        rc.update({"b": {"d": -1}})
        assert rc.get("b.d") == -1

    def test_keys_with_kwargs(self, rc):
        rc.update(d=-2, e=-3)
        assert rc.get("d") == -2
        assert rc.get("e") == -3

    def test_key_with_dot_notation(self, rc):
        rc.update({"b.d": -1})
        assert rc.get("b.d") == -1

    def test_key_with_tuple_notation(self, rc):
        rc.update({("b", "d"): -1})
        assert rc.get("b.d") == -1

    @pytest.mark.parametrize("trial", [123, {"z": 3}])
    def test_add(self, rc, trial):
        assert "n" not in rc._conf
        reloader = mock.Mock()
        rc.register("n", reloader)
        rc.update(n=trial)
        assert rc._conf["n"] == trial
        reloader.assert_called_with(Action.ADDED, None, trial)

    def test_delete_field(self, rc):
        assert "a" in rc._conf
        reloader = mock.Mock()
        rc.register("a", reloader)
        rc.update(a=REMOVE)
        assert "a" not in rc._conf
        reloader.assert_called_with(Action.REMOVED, 1, REMOVE)

    def test_invalid_args(self, rc):
        with pytest.raises(ValueError):
            rc.update(3)

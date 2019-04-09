import os
from collections.abc import MutableMapping
from tempfile import NamedTemporaryFile
from unittest import mock

import pytest

from resconfig.resconfig import Action
from resconfig.resconfig import REMOVE
from resconfig.resconfig import ResConfig
from resconfig.utils import expand


def reloaderfunc(*args):
    return args


@pytest.fixture
def default_config():
    yield {"a": 1, "b": {"c": 2}}


@pytest.fixture
def rc(default_config):
    yield ResConfig(default_config)


@pytest.fixture
def filename():
    f = NamedTemporaryFile(delete=False)
    filename = f.name
    yield filename
    os.remove(filename)


class TestCase:
    @pytest.fixture(scope="function", autouse=True)
    def setup(self, request, default_config):
        request.instance.default = default_config
        yield


class TestBasicAPI(TestCase):
    def test_init_with_reloaders(self):
        key = "a"
        rc = ResConfig(reloaders={key: reloaderfunc})
        assert reloaderfunc in rc._reloaders[key][rc.reloaderkey]

    @pytest.mark.parametrize(
        "key, expected",
        [("a", True), ("b.c", True), ("a.c", False), ("z", False), ("x.y.z", False)],
    )
    def test_contains(self, rc, key, expected):
        assert (key in rc) is expected


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
        cb.assert_called_with(Action.MODIFIED, self.default["b"], {"c": 2, "d": 4})

    def test_reload(self, rc):
        called = mock.Mock()

        @rc.reloader("b")
        def reloader_func(*args, **kwargs):
            called(*args, **kwargs)

        assert reloader_func in rc._reloaders["b"][rc.reloaderkey]

        rc.reload()
        called.assert_called_with(Action.RELOADED, self.default["b"], self.default["b"])


class TestIO(TestCase):
    def test_from_dict(self, rc):
        rc.read_from_dict(self.default)
        assert rc._conf == expand(self.default)

    def test_from_json(self, rc, filename):
        rc.save_to_json(filename)
        with open(filename) as f:
            content = f.read()
        assert '{"a": 1' in content

        rc = ResConfig()
        rc.read_from_json(filename)
        assert "b.c" in rc
        assert rc.get("b.c") == self.default["b"]["c"]

    def test_from_yaml(self, rc, filename):
        rc.save_to_yaml(filename)
        with open(filename) as f:
            content = f.read()
        print(content)
        assert "a: 1" in content

        rc = ResConfig()
        rc.read_from_yaml(filename)
        assert "b.c" in rc
        assert rc.get("b.c") == self.default["b"]["c"]


class TestGet(TestCase):
    def test(self, rc):
        assert rc.get("b.c") == self.default["b"]["c"]

    def test_default(self, rc):
        assert rc.get("non", "default") == "default"

    def test_without_default(self, rc):
        with pytest.raises(KeyError):
            rc.get("non")


class TestUpdate(TestCase):
    @pytest.mark.parametrize("key, expected", [("a", True), ("z", False)])
    def test_key_existence(self, rc, key, expected):
        assert (key in rc) is expected

    def test_keys_with_dict_notation(self, rc):
        rc.update({"b": {"d": -1}})
        assert rc.get("b.d") == -1
        assert rc.get("b") == {"c": 2, "d": -1}

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

    def test_invalid_args(self, rc):
        with pytest.raises(ValueError):
            rc.update(3)


class TestReloaderTrigger(TestCase):
    @pytest.mark.parametrize("trial", [123, {"z": 3}])
    def test_added(self, rc, trial):
        assert "n" not in rc._conf
        reloader = mock.Mock()
        rc.register("n", reloader)
        rc.update(n=trial)
        assert rc.get("n") == trial
        reloader.assert_called_with(Action.ADDED, None, trial)

    @pytest.mark.parametrize(
        "key, newval", [("a", 5), ("b.c", 5), ("b.c", {"d": 5}), ("b.c", {"d.e": 5})]
    )
    def test_modified(self, rc, key, newval):
        assert key in rc
        oldval = rc.get(key)
        reloader = mock.Mock()
        rc.register(key, reloader)
        rc.update({key: newval})
        expanded = expand(newval) if isinstance(newval, MutableMapping) else newval
        assert rc.get(key) == expanded
        reloader.assert_called_with(Action.MODIFIED, oldval, expanded)

    def test_removed(self, rc):
        assert "a" in rc._conf
        reloader = mock.Mock()
        rc.register("a", reloader)
        rc.update(a=REMOVE)
        assert "a" not in rc._conf
        reloader.assert_called_with(Action.REMOVED, 1, REMOVE)

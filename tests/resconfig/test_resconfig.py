import os
from collections.abc import MutableMapping
from tempfile import NamedTemporaryFile
from unittest import mock

import pytest
from resconfig.resconfig import REMOVE
from resconfig.resconfig import Action
from resconfig.resconfig import Missing
from resconfig.resconfig import ResConfig
from resconfig.utils import expand


def reloaderfunc(*args):
    return args


@pytest.fixture
def default_config():
    yield {
        "x1": 1,
        "x2": "text_x2",
        "x3": {
            "y1": 2,
            "y2": "text_x3.y2",
            "y3": {"z1": 3, "z2": "text_x3.y3.z2"},
            "y4": {"z1": 4, "z2": "text_x3.y4.z2"},
        },
        "x4": {
            "y1": 5,
            "y2": "text_x4.y2",
            "y3": {"z1": 6, "z2": "text_x4.y3.z2"},
            "y4": {"z1": 7, "z2": "text_x4.y4.z2"},
        },
    }


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
        [
            ("x1", True),
            ("x1.z1", False),
            ("x3.y1", True),
            ("x3.z1", False),
            ("z", False),
            ("x.y.z", False),
        ],
    )
    def test_contains(self, key, expected):
        conf = ResConfig(self.default)
        assert (key in conf) is expected

    def test_asdict(self):
        rc = ResConfig(self.default)
        result = rc.asdict()
        assert isinstance(result, dict)
        assert rc._conf == result


class TestReloadable(TestCase):
    def test_deregister_from_nonexisting_key(self):
        conf = ResConfig(self.default)
        with pytest.raises(KeyError):
            conf.deregister("missingkey")

    def test_deregister_nonexisting_reloader(self):
        conf = ResConfig(self.default)
        conf.register("key", lambda *args: args)
        with pytest.raises(ValueError):
            conf.deregister("key", lambda *args: args)

    def test_deregister_all(self):
        def f(*args):
            return args

        conf = ResConfig(self.default)
        conf.register("key", f)
        conf.deregister("key")
        with pytest.raises(KeyError):
            conf.deregister("key", f)

    def test_deregister_last_reloader(self):
        def f(*args):
            return args

        conf = ResConfig(self.default)
        conf.register("key", f)
        conf.deregister("key", f)
        with pytest.raises(KeyError):
            conf.deregister("key", f)

    def test_register(self):
        callback = mock.Mock()
        conf = ResConfig(self.default)
        conf.register("x3.y1", callback)
        conf.update({"x3": {"y1": -1}})
        callback.assert_called_with(Action.MODIFIED, self.default["x3"]["y1"], -1)

    def test_register_with_dictval(self):
        callback = mock.Mock()
        conf = ResConfig(self.default)
        conf.register("x3.y4", callback)
        conf.update({"x3.y4": {"dummy": 4}})
        callback.assert_called_with(
            Action.MODIFIED,
            self.default["x3"]["y4"],
            {"z1": 4, "z2": "text_x3.y4.z2", "dummy": 4},
        )

    def test_reload(self):
        called = mock.Mock()
        conf = ResConfig(self.default)

        @conf.reloader("x1")
        def reloader_func(*args, **kwargs):
            called(*args, **kwargs)

        assert reloader_func in conf._reloaders["x1"][conf.reloaderkey]

        conf.reload()
        called.assert_called_with(
            Action.RELOADED, self.default["x1"], self.default["x1"]
        )


class TestIO(TestCase):
    def test_from_dict(self):
        conf = ResConfig(self.default)
        conf.read_from_dict(self.default)
        assert conf._conf == expand(self.default)

    def test_from_json(self, filename):
        conf = ResConfig(self.default)
        conf.save_to_json(filename)
        with open(filename) as f:
            content = f.read()
        assert '{"x1": 1' in content

        conf = ResConfig()
        conf.read_from_json(filename)
        assert "x3.y1" in conf
        assert conf.get("x3.y1") == self.default["x3"]["y1"]

    def test_from_yaml(self, filename):
        conf = ResConfig(self.default)
        conf.save_to_yaml(filename)
        with open(filename) as f:
            content = f.read()
        assert "x1: 1" in content

        conf = ResConfig()
        conf.read_from_yaml(filename)
        assert "x3.y1" in conf
        assert conf.get("x3.y1") == self.default["x3"]["y1"]


class TestGet(TestCase):
    def test(self):
        conf = ResConfig(self.default)
        assert conf.get("x3.y1") == self.default["x3"]["y1"]

    def test_default(self):
        conf = ResConfig(self.default)
        assert conf.get("non", "default") == "default"

    def test_without_default(self):
        conf = ResConfig(self.default)
        with pytest.raises(KeyError):
            conf.get("non")

    def test_with_schema(self):
        key = "x3.y1"
        type = int
        trial = "123"
        conf = ResConfig(schema={key: type})
        conf.update({key: trial})
        v = conf.get(key)
        assert isinstance(v, type)
        assert v == type(trial)

    def test_with_schema_with_default(self):
        default = object()
        conf = ResConfig(schema={"a": int})
        assert "a" not in conf
        conf.get("a", default) is default

    def test_with_schema_with_error(self):
        conf = ResConfig(schema={"a": int})
        conf.update(a="xyz")
        with pytest.raises(ValueError) as exc:
            conf.get("a")
        assert "cannot be converted to" in str(exc)


class TestReplace(TestCase):
    newconf = {
        "x2": "foo",
        "x4": {"y4": {"z1": 3}, "y3": {"z1": {"foo": "bar"}}, "j": {"k": "foo"}},
        "y": "bar",
    }

    def test_args(self):
        a = ResConfig()
        a.replace(self.newconf)
        b = ResConfig()
        b.replace(**self.newconf)
        assert a.asdict() == b.asdict()

    def test_invalid_args(self):
        conf = ResConfig(self.default)
        with pytest.raises(TypeError):
            conf.replace("badarg")

    def test(self):
        conf = ResConfig(self.default)
        assert conf.asdict() != self.newconf
        conf.replace(self.newconf)
        assert conf.asdict() == self.newconf


class TestUpdate(TestCase):
    def test_keys_with_dict_notation(self):
        conf = ResConfig(self.default)
        conf.update({"x4": {"y4": {"z3": -1}}})
        assert conf.get("x4.y4.z3") == -1
        assert conf.get("x4.y4") == {"z1": 7, "z2": "text_x4.y4.z2", "z3": -1}

    def test_updating_nondict_with_dict(self):
        conf = ResConfig(self.default)
        key = "x3.y1"
        newval = {"foo": "bar"}
        assert not isinstance(conf.get(key), dict)
        conf.update({key: newval})
        assert conf.get(key) == newval

    def test_keys_with_kwargs(self):
        conf = ResConfig(self.default)
        conf.update(d=-2, e=-3)
        assert conf.get("d") == -2
        assert conf.get("e") == -3

    def test_key_with_dot_notation(self):
        conf = ResConfig(self.default)
        conf.update({"b.d": -1})
        assert conf.get("b.d") == -1

    def test_key_with_tuple_notation(self):
        conf = ResConfig(self.default)
        conf.update({("b", "d"): -1})
        assert conf.get("b.d") == -1

    def test_invalid_args(self):
        conf = ResConfig(self.default)
        with pytest.raises(ValueError):
            conf.update(3)


class TestReloaderTrigger(TestCase):
    @pytest.mark.parametrize("trial", [123, {"z": 3}])
    def test_added(self, trial):
        conf = ResConfig(self.default)
        assert "n" not in conf._conf
        reloader = mock.Mock()
        conf.register("n", reloader)
        conf.update(n=trial)
        assert conf.get("n") == trial
        reloader.assert_called_with(Action.ADDED, Missing, trial)

    @pytest.mark.parametrize(
        "key, newval",
        [("x1", 5), ("x3.y1", 5), ("x3.y4", {"z3": 5}), ("x3.y4", {"z3.w": 5})],
    )
    def test_modified(self, key, newval):
        conf = ResConfig(self.default)
        assert key in conf
        oldval = conf.get(key)
        reloader = mock.Mock()
        conf.register(key, reloader)
        conf.update({key: newval})
        if isinstance(newval, MutableMapping):
            expanded = expand(newval) if isinstance(newval, MutableMapping) else newval
            expanded = {**oldval, **expanded}
        else:
            expanded = newval
        assert conf.get(key) == expanded
        reloader.assert_called_with(Action.MODIFIED, oldval, expanded)

    def test_removed(self):
        conf = ResConfig(self.default)
        assert "x3" in conf
        reloader = mock.Mock()
        conf.register("x3", reloader)
        conf.update(x3=REMOVE)
        assert "x3" not in conf
        reloader.assert_called_with(Action.REMOVED, self.default["x3"], REMOVE)

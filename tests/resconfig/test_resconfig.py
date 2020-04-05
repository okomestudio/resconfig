from collections.abc import MutableMapping
from unittest import mock

import pytest
from resconfig.dicttype import expand
from resconfig.dicttype import isdict
from resconfig.dicttype import merge
from resconfig.dicttype import normkeyget
from resconfig.resconfig import Action
from resconfig.resconfig import ResConfig
from resconfig.resconfig import Sentinel


class TestCase:
    @pytest.fixture(scope="function", autouse=True)
    def setup(self, request, default_config):
        request.instance.default = default_config
        yield


class TestBasicAPI(TestCase):
    def test_init_with_files(self, filename):
        expected = {"a": {"b": "1"}}
        conf = ResConfig(expected)
        conf.save(filename)
        conf = ResConfig(paths=["somenonexistingfile", filename])
        assert conf.asdict() == expected

    def test_init_with_watcher(self):
        def watcher(*args):
            return

        key = "a"
        conf = ResConfig(watchers={key: watcher})
        assert watcher in conf.watchers(key)

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


class TestWatchable(TestCase):
    def test_deregister_from_nonexisting_key(self):
        conf = ResConfig(self.default)
        with pytest.raises(KeyError):
            conf.deregister("missingkey")

    def test_deregister_nonexisting_watcher(self):
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

    def test_deregister_last_watcher(self):
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

        @conf.watch("x1")
        def watch_func(*args, **kwargs):
            called(*args, **kwargs)

        assert watch_func in conf.watchers("x1")

        conf.reload()
        called.assert_called_with(
            Action.RELOADED, self.default["x1"], self.default["x1"]
        )


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
        with pytest.raises(TypeError) as exc:
            conf.update(a="xyz")
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
        with pytest.raises(TypeError):
            conf.update(3)


class TestWatchersOnUpdate(TestCase):
    @pytest.mark.parametrize(
        "key, newval",
        [
            ("n", 123),
            ("n", {"z": 3}),
            ("x1.y1", 4),
            ("x1.y1.z1", 4),
            ("x1.y1.z1", {"foo": "bar"}),
        ],
    )
    def test_added(self, key, newval):
        conf = ResConfig(self.default)
        assert key not in conf
        watcher = mock.Mock()
        conf.register(key, watcher)
        conf.update({key: newval})
        assert conf.get(key) == newval
        watcher.assert_called_with(Action.ADDED, Sentinel.Missing, newval)

    @pytest.mark.parametrize(
        "key, newval",
        [("x1", 5), ("x3.y1", 5), ("x3.y4", {"z3": 5}), ("x3.y4", {"z3.w": 5})],
    )
    def test_modified(self, key, newval):
        conf = ResConfig(self.default)
        assert key in conf
        watcher = mock.Mock()
        conf.register(key, watcher)
        oldval = conf.get(key)
        conf.update({key: newval})
        if isdict(newval):
            expanded = merge(oldval, expand(newval))
        else:
            expanded = newval
        assert conf.get(key) == expanded
        watcher.assert_called_with(Action.MODIFIED, oldval, expanded)

    @pytest.mark.parametrize(
        "key, removed, remain",
        [
            ("x1", ["x1"], ["x2"]),
            ("x2", ["x2"], ["x1"]),
            ("x3", ["x3", "x3.y1", "x3.y2.z2"], ["x4"]),
            ("x3.y1", ["x3.y1"], ["x3.y2"]),
            ("x3.y4", ["x3.y4", "x3.y4.z1"], ["x3.y3"]),
            ("x3.y4.z2", ["x3.y4.z2"], ["x3.y4", "x3.y4.z1"]),
        ],
    )
    def test_removed_with_sentinel(self, key, removed, remain):
        conf = ResConfig(self.default)
        assert key in conf
        watcher = mock.Mock()
        conf.register(key, watcher)
        conf.update({key: Sentinel.REMOVE})
        for k in removed:
            assert k not in conf
        for k in remain:
            assert k in conf
        watcher.assert_called_with(
            Action.REMOVED, normkeyget(self.default, key), Sentinel.REMOVE
        )

    def test_removed(self, default_config_key, all_default_config_keys):
        key = default_config_key
        conf = ResConfig(self.default)
        assert key in conf
        oldval = normkeyget(self.default, key)
        watcher = mock.Mock()
        conf.register(key, watcher)
        conf.update({key: Sentinel.REMOVE})
        # TODO: Test non-existence of removed keys
        # TODO: Test existence of remaining keys
        watcher.assert_called_with(Action.REMOVED, oldval, Sentinel.REMOVE)

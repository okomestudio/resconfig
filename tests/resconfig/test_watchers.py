from unittest import mock

import pytest
from resconfig import ResConfig
from resconfig.actions import Action
from resconfig.dicttype import expand
from resconfig.dicttype import isdict
from resconfig.dicttype import merge
from resconfig.dicttype import normkeyget
from resconfig.resconfig import Sentinel

from .test_resconfig import TestCase


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

        assert watch_func in conf._watchers.funcs("x1")

        conf.reload()
        called.assert_called_with(
            Action.RELOADED, self.default["x1"], self.default["x1"]
        )


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
        watcher.assert_called_with(Action.ADDED, Sentinel.MISSING, newval)

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
            expanded = merge(deepcopy(oldval), expand(newval))
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

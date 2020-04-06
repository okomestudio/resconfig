from copy import deepcopy
from unittest import mock

import pytest
from resconfig import ResConfig
from resconfig.actions import Action
from resconfig.dicttype import Dict
from resconfig.dicttype import get
from resconfig.dicttype import isdict
from resconfig.dicttype import merge
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

    def test_watch_decorator(self):
        key = "x3.y2"
        called = mock.Mock()
        conf = ResConfig(self.default)

        @conf.watch(key)
        def watch_func(*args, **kwargs):
            called(*args, **kwargs)

        assert watch_func in conf._watchers.funcs(key)
        conf.reload()
        val = get(self.default, key)
        called.assert_called_with(Action.RELOADED, val, val)


class TestReload(TestCase):
    def test(self):
        watchers = {
            "x1": mock.Mock(),
            "x2": mock.Mock(),
            "x3": mock.Mock(),
            "x3.y1": mock.Mock(),
            "x3.y2": mock.Mock(),
            "x3.y3": mock.Mock(),
            "x3.y3.z1": mock.Mock(),
            "x3.y3.z2": mock.Mock(),
            "x3.y4": mock.Mock(),
            "x3.y4.z1": mock.Mock(),
            "x3.y4.z2": mock.Mock(),
            "x4.y1": mock.Mock(),
            "x4.y2": mock.Mock(),
            "x4.y3": mock.Mock(),
            "x4.y3.z1": mock.Mock(),
            "x4.y3.z2": mock.Mock(),
            "x4.y4": mock.Mock(),
            "x4.y4.z1": mock.Mock(),
            "x4.y4.z2": mock.Mock(),
            "foo.bar": mock.Mock(),
        }
        conf = ResConfig(self.default, watchers=watchers)

        for key, func in watchers.items():
            if key not in conf:
                func.assert_not_called
            else:
                v = get(self.default, key)
                func.assert_called_with(Action.ADDED, Sentinel.MISSING, v)
                assert func.call_count == 1

        conf.reload()

        for key, func in watchers.items():
            if key not in conf:
                func.assert_not_called
            else:
                v = get(self.default, key)
                func.assert_called_with(Action.RELOADED, v, v)
                assert func.call_count == 2


class TestUpdate(TestCase):
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
        "key, newval, expected",
        [
            ("x1", 5, 5),
            ("x3.y1", 5, 5),
            ("x3.y4", {"z3": 5}, {"z1": 4, "z2": "text_x3.y4.z2", "z3": 5}),
            ("x3.y4", {"z3.w": 5}, {"z1": 4, "z2": "text_x3.y4.z2", "z3": {"w": 5}}),
            ("x3.y3", 4, 4),
        ],
    )
    def test_modified(self, key, newval, expected):
        conf = ResConfig(self.default)
        assert key in conf
        watcher = mock.Mock()
        conf.register(key, watcher)
        oldval = conf.get(key)
        conf.update({key: newval})
        assert conf.get(key) == expected
        watcher.assert_called_with(Action.MODIFIED, oldval, expected)

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
            Action.REMOVED, get(self.default, key), Sentinel.REMOVE
        )

    def test_removed(self, default_config_key, all_default_config_keys):
        key = default_config_key
        conf = ResConfig(self.default)
        assert key in conf
        oldval = get(self.default, key)
        watcher = mock.Mock()
        conf.register(key, watcher)
        conf.update({key: Sentinel.REMOVE})
        # TODO: Test non-existence of removed keys
        # TODO: Test existence of remaining keys
        watcher.assert_called_with(Action.REMOVED, oldval, Sentinel.REMOVE)

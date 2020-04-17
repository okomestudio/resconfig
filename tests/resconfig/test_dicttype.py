from copy import deepcopy

import pytest
from resconfig.dicttype import Dict
from resconfig.dicttype import merge
from resconfig.dicttype import normalize
from resconfig.dicttype import normkey


class TestDict:
    default = {"foo": {"bar": {"baz": 0}, "qux": "quux"}}

    @pytest.fixture
    def d(self):
        yield Dict(deepcopy(self.default))

    @pytest.mark.parametrize(
        "key, expected",
        [
            ("foo", True),
            ("foo.bar", True),
            ("foo.bar.baz", True),
            ("foo.bar.baz.qux", False),
            ("foo.baz", False),
            ("bar", False),
            ("bar.baz", False),
        ],
    )
    def test_contains(self, d, key, expected):
        assert (key in d) is expected
        assert (tuple(key.split(".")) in d) is expected

    @pytest.mark.parametrize(
        "key, expected", [("foo", {}), ("foo.bar", {"foo": {"qux": "quux"}})]
    )
    def test_delitem(self, d, key, expected):
        del d[key]
        assert key not in d
        assert d == expected

    @pytest.mark.parametrize("key", ["foo.baz", "bar"])
    def test_delitem_error(self, d, key):
        with pytest.raises(KeyError) as exc:
            del d[key]
        assert f"'{key}'" in str(exc.value)

    @pytest.mark.parametrize(
        "key, expected",
        [
            ("foo", {"bar": {"baz": 0}, "qux": "quux"}),
            ("foo.bar", {"baz": 0}),
            ("foo.bar.baz", 0),
            ("foo.qux", "quux"),
        ],
    )
    def test_getitem(self, d, key, expected):
        assert d[key] == expected

    @pytest.mark.parametrize("key", ["bar", "foo.buz", "foo.bar.qux", "bar.foo"])
    def test_getitem_error(self, d, key):
        with pytest.raises(KeyError):
            _ = d[key]

    @pytest.mark.parametrize(
        "key, value, expected",
        [
            ("foo", 3, {"foo": 3}),
            ("foo.bar", "qux", {"foo": {"bar": "qux", "qux": "quux"}}),
        ],
    )
    def test_setitem(self, d, key, value, expected):
        d[key] = value
        assert d == expected

    @pytest.mark.parametrize("key", ["foo.buz.bar", "foo.bar.qux.quux"])
    def test_setitem_error(self, d, key):
        with pytest.raises(KeyError):
            d[key] = object()

    @pytest.mark.parametrize(
        "args, kwargs, expected",
        [
            (["foo"], {}, {"bar": {"baz": 0}, "qux": "quux"}),
            (["foo.bar"], {}, {"baz": 0}),
            (["foo.bar.baz"], {}, 0),
            (["foo.bar.quux.buz"], {"default": "baz"}, "baz"),
            (["bar"], {}, None),
            (["bar"], {"default": "baz"}, "baz"),
        ],
    )
    def test_get(self, d, args, kwargs, expected):
        assert d.get(*args, **kwargs) == expected

    @pytest.mark.parametrize(
        "key, kwargs, popped, expected",
        [
            ("foo", {}, {"bar": {"baz": 0}, "qux": "quux"}, {}),
            ("foo.bar", {}, {"baz": 0}, {"foo": {"qux": "quux"}}),
            ("foo.bar.baz", {}, 0, {"foo": {"bar": {}, "qux": "quux"}}),
            (
                "bar",
                {"d": "popthis"},
                "popthis",
                {"foo": {"bar": {"baz": 0}, "qux": "quux"}},
            ),
            (
                "foo.buz.qux.bar",
                {"d": "popthis"},
                "popthis",
                {"foo": {"bar": {"baz": 0}, "qux": "quux"}},
            ),
        ],
    )
    def test_pop(self, d, key, kwargs, popped, expected):
        assert d.pop(key, **kwargs) == popped
        assert d == expected

    @pytest.mark.parametrize(
        "key, expected", [("bar", KeyError), ("foo.qux.bar", TypeError)]
    )
    def test_pop_error(self, d, key, expected):
        with pytest.raises(expected):
            d.pop(key)

    @pytest.mark.parametrize(
        "key, kwargs, got, expected",
        [
            ("foo", {}, default["foo"], default),
            ("bar", {}, None, {**default, **{"bar": None}}),
            ("bar", {"default": "foo"}, "foo", {**default, **{"bar": "foo"}}),
            (
                "foo.bar.qux",
                {"default": "foo"},
                "foo",
                {"foo": {"bar": {"baz": 0, "qux": "foo"}, "qux": "quux"}},
            ),
        ],
    )
    def test_setdefault(self, d, key, kwargs, got, expected):
        assert d.setdefault(key, **kwargs) == got
        assert d == expected

    @pytest.mark.parametrize(
        "key, expected",
        [("foo.bar.qux.quux", KeyError), ("foo.bar.baz.qux", TypeError)],
    )
    def test_setdefault_error(self, d, key, expected):
        with pytest.raises(expected):
            d.setdefault(key)

    @pytest.mark.parametrize(
        "args, kwargs, expected",
        [
            (({"bar": 3},), {}, {**default, **{"bar": 3}}),
            (({"foo": 1, "bar.baz": 3},), {}, {"foo": 1, "bar": {"baz": 3}}),
            (({"foo.baz.bar": 1},), {}, {"foo": {"baz": {"bar": 1}}}),
            ([(("bar", 3),)], {}, {**default, **{"bar": 3}}),
            ([(("foo", 1), ("bar.baz", 3))], {}, {"foo": 1, "bar": {"baz": 3}}),
            ([(("foo.baz.bar", 1),)], {}, {"foo": {"baz": {"bar": 1}}}),
            ([], {"bar": 3}, {**default, **{"bar": 3}}),
            ([], {"foo": 1, "bar.baz": 3}, {"foo": 1, "bar": {"baz": 3}}),
            ([], {"foo.baz.bar": 1}, {"foo": {"baz": {"bar": 1}}}),
        ],
    )
    def test_update(self, d, args, kwargs, expected):
        d.update(*args, **kwargs)
        assert d == expected

    def test_update_error(self, d):
        with pytest.raises(TypeError):
            d.update({"foo": "bar"}, 1)

    @pytest.mark.parametrize(
        "args, kwargs, expected",
        [
            ((["foo", "bar", "baz"],), {}, {"foo": None, "bar": None, "baz": None}),
            ((["foo", "bar", "baz"],), {"value": 0}, {"foo": 0, "bar": 0, "baz": 0}),
            (
                (["foo.bar", "bar", "baz"],),
                {"value": 0},
                {"foo": {"bar": 0}, "bar": 0, "baz": 0},
            ),
            (
                (["foo.bar.baz", "bar", "foo.bar.qux"],),
                {"value": 0},
                {"foo": {"bar": {"baz": 0, "qux": 0}}, "bar": 0},
            ),
        ],
    )
    def test_fromkeys(self, d, args, kwargs, expected):
        assert d.fromkeys(*args, **kwargs) == expected

    def test_allkeys(self, d):
        assert list(d.allkeys()) == [("foo", "bar", "baz"), ("foo", "qux")]
        assert list(d.allkeys(as_str=True)) == ["foo.bar.baz", "foo.qux"]


class TestMerge:
    @pytest.mark.parametrize(
        "d1, d2, expected",
        [
            ({"a": 1}, {"b": 2}, {"a": 1, "b": 2}),
            ({"a": {"x": 3}}, {"a": 2}, {"a": 2}),
            ({"a": 2}, {"a": {"x": 3}}, {"a": {"x": 3}}),
            ({"a": {"b": 1}}, {"a": {"c": 2}}, {"a": {"b": 1, "c": 2}}),
        ],
    )
    def test(self, d1, d2, expected):
        objid = id(d1)
        result = merge(d1, d2)
        assert result == expected
        assert id(result) == objid


class TestNormalize:
    @pytest.mark.parametrize(
        "trial, expected",
        [
            ({"a.b.c": 1}, {"a": {"b": {"c": 1}}}),
            ({"a.b.c": 1, "a": {"b": {"d": 2}}}, {"a": {"b": {"c": 1, "d": 2}}}),
            ({("a", "b", "c"): 1}, {"a": {"b": {"c": 1}}}),
            (
                {("a", "b", "c"): 1, "a": {"b": {"d": 2}}},
                {"a": {"b": {"c": 1, "d": 2}}},
            ),
            ({"a.b": {"c.d": 1}}, {"a": {"b": {"c": {"d": 1}}}}),
        ],
    )
    def test(self, trial, expected):
        assert normalize(trial) == expected

    @pytest.mark.parametrize("trial", [{"a": 1, "a.b": 2}, {"a.b": 1, "a.b.c": 2}])
    def test_inconsistent(self, trial):
        with pytest.raises(TypeError) as exc:
            print(normalize(trial))
        assert "cannot convert" in str(exc)


class TestNormkey:
    @pytest.mark.parametrize(
        "key, expected",
        [("a", ["a"]), ("a.b.c", ["a", "b", "c"]), (("a", "b", "c"), ["a", "b", "c"])],
    )
    def test(self, key, expected):
        assert list(normkey(key)) == expected

    @pytest.mark.parametrize("key, expected", [(3, TypeError), (["a", "b"], TypeError)])
    def test_error(self, key, expected):
        with pytest.raises(expected):
            list(normkey(key))

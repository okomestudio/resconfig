import pytest

from resconfig.utils import expand
from resconfig.utils import merge


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
        assert merge(d1, d2) == expected


class TestExpand:
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
        ],
    )
    def test(self, trial, expected):
        assert expand(trial) == expected

    @pytest.mark.parametrize("trial", [{"a": 1, "a.b": 2}])
    def test_inconsistent(self, trial):
        with pytest.raises(ValueError) as exc:
            expand(trial)
        assert "Cannot upcast" in str(exc)

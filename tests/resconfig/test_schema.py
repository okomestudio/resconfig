import pytest
from resconfig import ResConfig


class TestInit:
    @pytest.mark.parametrize(
        "key, vtype, expected", [("x1", int, 1), ("x3.y4.z1", str, "4")]
    )
    def test(self, default_config, key, vtype, expected):
        conf = ResConfig(default_config, schema={key: vtype})
        result = conf.get(key)
        assert result == expected
        assert isinstance(result, vtype)

    @pytest.mark.parametrize(
        "key, vtype, expected", [("x2", int, TypeError), ("x3.y2", float, TypeError)]
    )
    def test_with_error(self, default_config, key, vtype, expected):
        with pytest.raises(expected):
            ResConfig(default_config, schema={key: vtype})


class TestUpdate:
    @pytest.mark.parametrize(
        "key, vtype, value, expected",
        [("x1", str, 123, "123"), ("x3.y1", int, "123", 123)],
    )
    def test(self, key, vtype, value, expected):
        conf = ResConfig(schema={key: vtype})
        conf.update({key: value})
        result = conf.get(key)
        assert result == expected
        assert isinstance(result, vtype)

    @pytest.mark.parametrize(
        "key, vtype, value, expected",
        [("x1", int, "foo", TypeError), ("z1", float, "foo", TypeError)],
    )
    def test_with_error(self, key, vtype, value, expected):
        conf = ResConfig(schema={key: vtype})
        with pytest.raises(expected) as exc:
            conf.update({key: value})
        assert "cannot be converted to" in str(exc)

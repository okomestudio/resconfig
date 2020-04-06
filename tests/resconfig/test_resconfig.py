import pytest
from resconfig.resconfig import ResConfig


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
        conf = ResConfig(config_paths=["somenonexistingfile", filename])
        assert conf._asdict() == expected

    def test_init_with_watcher(self):
        def watcher(*args):
            return

        key = "a"
        conf = ResConfig(watchers={key: watcher})
        assert watcher in conf._watchers.funcs(key)

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
        result = rc._asdict()
        assert isinstance(result, dict)
        assert rc._conf == result


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
        assert a._asdict() == b._asdict()

    def test_invalid_args(self):
        conf = ResConfig(self.default)
        with pytest.raises(TypeError):
            conf.replace("badarg")

    def test(self):
        conf = ResConfig(self.default)
        assert conf._asdict() != self.newconf
        conf.replace(self.newconf)
        assert conf._asdict() == self.newconf


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

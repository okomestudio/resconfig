from resconfig import ResConfig

from .test_resconfig import TestCase


class TestIO(TestCase):
    def test_from_json(self, filename):
        conf = ResConfig(self.default)
        conf.save_to_json(filename)
        with open(filename) as f:
            content = f.read()
        assert '{"x1": 1' in content

        conf = ResConfig()
        conf.load_from_json(filename)
        assert "x3.y1" in conf
        assert conf.get("x3.y1") == self.default["x3"]["y1"]

    def test_from_yaml(self, filename):
        conf = ResConfig(self.default)
        conf.save_to_yaml(filename)
        with open(filename) as f:
            content = f.read()
        assert "x1: 1" in content

        conf = ResConfig()
        conf.load_from_yaml(filename)
        assert "x3.y1" in conf
        assert conf.get("x3.y1") == self.default["x3"]["y1"]

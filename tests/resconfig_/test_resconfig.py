from resconfig.resconfig import ResConfig


class TestResConfig:
    default = {"a": 1, "b": {"c": 2}}

    def test(self):
        config = ResConfig(self.default)
        assert config.get("b.c") == self.default["b"]["c"]

    def test_register(self):
        config = ResConfig(self.default)
        config.register("b.c", lambda x: x)

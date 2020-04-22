from io import StringIO


class BaseTestLoad:
    module = None

    def test_empty(self):
        stream = StringIO("")
        loaded = self.module.load(stream)
        assert loaded == {}, "Blank file should load as an empty dict"
